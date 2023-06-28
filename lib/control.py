from connect import *
import asyncio
import logging
import zmq
import zmq.asyncio
import json
import numpy as np
from lib.component_protos.sound_alsa import SaStatePlayBack as PBState

logger = logging.getLogger(__name__)


async def feed(interval):
    start = asyncio.create_task(
        catch('stepper-motor',
              lambda pub: pub.running,
              lambda x: True,
              timeout=100)
    )
    await Request(request_type="ChangeState",
                  component='stepper-motor',
                  body={'running': True, 'direction': True}).send_and_wait()
    await start

    await catch('stepper-motor',
                lambda pub: not pub.running,
                lambda x: True,
                timeout=interval)
    return


async def cue(pos, color):
    asyncio.create_task(
        catch(pos,
              lambda pub: pub.led_state == color,
              lambda x: True,
              timeout=100)
    )
    await Request(request_type="ChangeState",
                  component=pos,
                  body={'led_state': color}).send_and_wait()
    return


class Sun:
    def __init__(self, interval):
        self.brightness = 0
        self.daytime = False
        self.interval = interval

    async def cycle(self, **kwargs):
        await Request(request_type="SetParameters",
                      component='house-light',
                      body={'clock_interval': self.interval}
                      ).send_and_wait()
        interval_check = await Request(request_type="GetParameters",
                                       component='house-light',
                                       body=None).send_and_wait()
        if interval_check.clock_interval != self.interval:
            raise f"House-Light Clock Interval not set to {self.interval}"

        async def light_update(msg):
            self.brightness = msg.brightness
            self.daytime = msg.daytime
            return True

        while True:
            await catch('house-light', light_update, lambda x: None, timeout=self.interval+1)


async def blip(brightness, interval, **kwargs):
    ctx = kwargs['context'] or zmq.asyncio.Context.instance()
    logger.debug("Setting House Lights")
    asyncio.create_task(
        catch('house-light',
              lambda pub: True if pub.brightness == brightness else False,
              lambda x: True,
              timeout=100)
    )
    await Request(request_type="ChangeState",
                  component='house-light',
                  body={'manual': True, 'brightness': brightness}
                  ).send_and_wait()

    await asyncio.sleep(interval)
    await Request(request_type="ChangeState",
                  component='house-light',
                  body={'manual': False, 'ephemera': True}
                  ).send_and_wait()
    asyncio.create_task(
        catch('house-light',
              lambda pub: not pub.manual,
              lambda x: True,
              timeout=100)
    )
    return


class PlayBack:
    def __init__(self, conf_fs, **kwargs):
        with open(conf_fs) as f:
            config = json.load(f)
            self.dir = config['stimulus_root']
            self.stim_data = config['stimuli']

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
        await Request(request_type="SetParameters",
                      component='audio-playback',
                      body={'audio_dir': conf_fs}
                      ).send_and_wait()
        dir_check = await Request(request_type="GetParameters",
                                  component='audio-playback',
                                  body=None,
                                  ).send_and_wait()
        if dir_check.audio_dir != conf_fs:
            raise "AUDIO DIRECTORY MISMATCH?"

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
                  lambda pub: (pub.audio_id == stim) & (pub.playback == PBState.PLAYING),
                  lambda x: True,
                  timeout=100)
        )
        await Request(request_type="ChangeState",
                      component='audio-playback',
                      body={'audio_id': stim, 'playback': PBState.PLAYING}
                      ).send_and_wait()
        await pub_confirmation

        completion = asyncio.create_task(
            catch('audio-playback',
                  lambda pub: (pub.playback == PBState.STOPPED),
                  lambda x: True,
                  timeout=6000)
        )
        return completion

    def stop(self, context=None):
        pub_confirmation = asyncio.create_task(
            catch('audio-playback',
                  lambda pub: (pub.playback == PBState.STOPPED),
                  lambda x: True,
                  timeout=100)
        )
        await Request(request_type="ChangeState",
                      component='audio-playback',
                      body={'playback': PBState.STOPPED}
                      ).send_and_wait()
        await pub_confirmation
        return
