from bind import *
import asyncio
import logging
import zmq
import zmq.asyncio
import json
import numpy as np
from lib.component_protos.sound_alsa import SaStatePlayBack as PBState
from lib.errata import *
from lib.control import *

logger = logging.getLogger(__name__)


async def feed(duration, **kwargs):
    start = asyncio.create_task(
        catch('stepper-motor',
              caught=lambda pub: pub.running,
              failure=lambda i: pub_err("stepper-motor") if not i else None,
              timeout=TIMEOUT,
              **kwargs)
    )
    req = await Request.spawn(request_type="ChangeState",
                              component='stepper-motor',
                              body={'running': True, 'direction': True})
    await req.send()
    await start

    await catch('stepper-motor',
                caught=lambda pub: not pub.running,
                failure=lambda i: pub_err("stepper-motor") if not i else None,
                timeout=duration + TIMEOUT,
                **kwargs)
    return


async def cue(pos, color):
    asyncio.create_task(
        catch(pos,
              caught=lambda pub: pub.led_state == color,
              failure=lambda i: pub_err(pos) if not i else None,
              timeout=TIMEOUT)
    )
    req = await Request.spawn(request_type="ChangeState",
                              component=pos,
                              body={'led_state': color})
    await req.send()
    return


class Sun:
    @classmethod
    async def spawn(cls, interval):
        logger.debug("Sun spawning")
        self = Sun()
        self.brightness = 0
        self.daytime = False
        self.interval = interval
        return self

    async def cycle(self, **kwargs):
        logger.debug("Sun cycle initiating")
        param_set = await Request.spawn(request_type="SetParameters",
                                        component='house-light',
                                        body={'clock_interval': self.interval}
                                        )
        await param_set.send()

        interval_check = await Request.spawn(request_type="GetParameters",
                                             component='house-light',
                                             body=None)
        check_res = await interval_check.send()
        if check_res.clock_interval != self.interval:
            raise f"House-Light Clock Interval not set to {self.interval}"

        def light_update(msg):
            self.brightness = msg.brightness
            self.daytime = msg.daytime
            return True

        while True:
            await catch('house-light',
                        caught=light_update,
                        failure=lambda i: pub_err("house-light") if not i else None,
                        timeout=self.interval + 1)


async def blip(brightness, interval, **kwargs):
    ctx = kwargs['context'] or zmq.asyncio.Context.instance()
    logger.debug("Setting House Lights")
    asyncio.create_task(
        catch('house-light',
              caught=lambda pub: True if pub.brightness == brightness else False,
              failure=lambda i: pub_err("house-light") if not i else None,
              timeout=100)
    )
    req = await Request.spawn(request_type="ChangeState",
                              component='house-light',
                              body={'manual': True, 'brightness': brightness}
                              )
    await req.send()

    await asyncio.sleep(interval)

    asyncio.create_task(
        catch('house-light',
              lambda pub: not pub.manual,
              lambda i: pub_err("house-light") if not i else None,
              timeout=100)
    )
    req2 = await Request.spawn(request_type="ChangeState",
                               component='house-light',
                               body={'manual': False, 'ephemera': True}
                               )
    await req2.send()
    return


class PlayBack:
    @classmethod
    async def spawn(cls, conf_fs, **kwargs):
        self = PlayBack()
        with open(conf_fs) as f:
            cf = json.load(f)
            self.dir = cf['stimulus_root']
            self.stim_data = cf['stimuli']

        self.cue_locations = {}
        playlist = []
        # Validate Stimuli List & Store Cue Location
        # Also create playlist
        for i, stim in enumerate(self.stim_data):

            cue_loc = None
            for action, consq in stim['responses'].items():
                total = (consq['p_reward'] if 'p_reward' in consq else 0) + \
                        (consq['p_punish'] if 'p_punish' in consq else 0)
                if total > 1:
                    logger.error(f"Reward/Punish Percentage Exceed 1.0 for {action} in {stim['name']}")
                    raise
                if 'p_reward' in consq:
                    cue_loc = action
            self.cue_locations[stim['name']] = cue_loc
            playlist.append(np.repeat(i, stim['frequency']))

        self.playlist = np.array(playlist).flatten()
        if kwargs['shuffle']:
            np.random.shuffle(self.playlist)

        # Request controller to import stimuli
        params = await Request.spawn(request_type="SetParameters",
                                     component='audio-playback',
                                     body={'audio_dir': conf_fs}
                                     )
        await params.send()
        dir_check = await Request.spawn(request_type="GetParameters",
                                        component='audio-playback',
                                        body=None,
                                        )
        check_res = await dir_check.send()
        if check_res.audio_dir != conf_fs:
            raise "AUDIO DIRECTORY MISMATCH?"
        return self

    def __iter__(self):
        self.iter = iter(self.playlist)
        self.playing = False
        self.stimulus = None
        return self

    def __next__(self):
        item = next(self.iter)
        self.stimulus = self.stim_data[item]['name']
        return self.stim_data[item]

    async def current_cue(self):
        if self.stimulus is None:
            logger.error("Trying to determine cue but no stimulus specified. Try initiating playlist first")
            raise
        return self.cue_locations[self.stimulus]

    async def play(self, stim=None):
        if stim is None:
            stim = self.stimulus

        pub_confirmation = asyncio.create_task(
            catch('audio-playback',
                  caught=lambda pub: (pub.audio_id == stim) & (pub.playback == PBState.PLAYING),
                  failure=lambda i: pub_err("sound-alsa") if not i else None,
                  timeout=100)
        )
        req = await Request.spawn(request_type="ChangeState",
                                  component='audio-playback',
                                  body={'audio_id': stim, 'playback': PBState.PLAYING}
                                  )
        await req.send()
        await pub_confirmation
        self.playing = True

        completion = asyncio.create_task(
            catch('audio-playback',
                  caught=lambda pub: (pub.playback == PBState.STOPPED),
                  failure=lambda i: pub_err("audio-playback") if not i else None,
                  timeout=6000)
        )
        return completion

    async def stop(self, context=None):
        pub_confirmation = asyncio.create_task(
            catch('audio-playback',
                  lambda pub: (pub.playback == PBState.STOPPED),
                  failure=lambda i: pub_err("audio-playback") if not i else None,
                  timeout=100)
        )
        req = await Request.spawn(request_type="ChangeState",
                                  component='audio-playback',
                                  body={'playback': PBState.STOPPED}
                                  )
        await req.send()
        await pub_confirmation
        self.playing = False
        return
