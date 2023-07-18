import asyncio
import logging
import zmq.asyncio
import json
import numpy as np
from .errata import *
from .relay import Sauron
from .inform import *
import yaml

logger = logging.getLogger(__name__)


class Morgoth:
    def __init__(self):
        self.messenger = None

    @classmethod
    async def spawn(cls, messenger: Sauron):
        self = Morgoth()
        self.messenger = messenger

    async def set_feeder(self, duration):
        logger.debug("Setting feed duration")
        await self.messenger.request(request_type="SetParameters",
                                     component='stepper-motor',
                                     body={'timeout': duration}
                                     )

        interval_check = await self.messenger.request(request_type="GetParameters",
                                                      component='stepper-motor',
                                                      body=None)
        if interval_check.timeout != duration:
            logger.error(f"Stepper motor timeout parameter not set to {duration}")

    async def feed(self, delay=0):
        logger.debug('feed() called, requesting stepper motor')
        await asyncio.sleep(delay)
        await self.messenger.request(request_type="ChangeState",
                                     component='stepper-motor',
                                     body={'running': True, 'direction': True})
        await self.messenger.scry('stepper-motor',
                                  condition=lambda p: p.running,
                                  failure=pub_err,
                                  timeout=TIMEOUT)
        logger.debug('feeding confirmed by decide-rs, awaiting motor stop')
        await self.messenger.scry('stepper-motor',
                                  condition=lambda pub: not pub.running,
                                  failure=pub_err,
                                  timeout=TIMEOUT)
        logger.debug('motor stop confirmed by decide-rs')
        return

    async def cue(self, loc, color):
        pos = peck_parse(loc, mode='l')
        logger.debug(f'Requesting cue {pos}')
        await self.messenger.request(request_type="ChangeState",
                                     component=pos,
                                     body={'led_state': color})
        await self.messenger.scry(pos,
                                  condition=lambda pub: not pub.running,
                                  failure=pub_err,
                                  timeout=TIMEOUT)
        return

    async def keep_alight(self, interval):
        self.sun = Sun()
        await self.messenger.request(request_type="SetParameters",
                                     component='house-light',
                                     body={'clock_interval': interval})
        interval_check = await self.messenger.request(request_type="GetParameters",
                                                      component='house-light',
                                                      body=None)
        if interval_check.clock_interval != interval:
            logger.error(f"House-Light Clock Interval not set to {interval},"
                         f" got {interval_check.clock_interval}")

        while True:
            self.messenger.scry('house-light', self.sun.update)
            await asyncio.sleep(10)

    async def blip(self, duration, brightness=0):
        logger.debug("Manually changing house lights")
        await self.messenger.request(request_type="ChangeState",
                                     component='house-light',
                                     body={'manual': True, 'brightness': brightness})
        await self.messenger.scry(
            'house-light',
            condition=lambda pub: True if pub.brightness == brightness else False,
            failure=pub_err,
            timeout=TIMEOUT
        )
        logger.debug("Manually changing house lights confirmed by decide-rs.")

        await asyncio.sleep(duration)

        logger.debug("Returning house lights to cycle")
        self.messenger.request(request_type="ChangeState",
                               component='house-light',
                               body={'manual': False, 'ephemera': True}
                               )
        await self.messenger.scry(
            'house-light',
            condition=lambda pub: not pub.manual,
            failure=pub_err,
            timeout=TIMEOUT
        )
        logger.debug("Returning house lights to cycle succeeded")

    async def play(self, stim):

    async def stop(self, stim):

class Sun:
    def __init__(self):
        self.manual = False
        self.dyson = True
        self.brightness = 0
        self.daytime = True

    def update(self, decoded):
        logger.debug("Updating House-Light from PUB")
        for key, val in decoded.items():
            setattr(self, key, val)
        return True


class JukeBox:
    def __init__(self):
        self.playing = False
        self.stimulus = None
        self.stim_duration = None
        self.stim_data = None
        self.sample_rate = None
        self.ptr = None
        self.shuffle = True
        self.replace = False

    @classmethod
    async def spawn(cls, conf_fs, shuffle=True, replace=False, get_cues=True):
        logger.info("Spawning Playback Machine")
        self = JukeBox()
        with open(conf_fs) as file:
            cf = json.load(file)
            self.dir = cf['stimulus_root']
            self.stim_data = cf['stimuli']

        self.cue_locations = {}
        playlist = []

        logger.debug("Validating and generating playlist")
        for i, stim in enumerate(self.stim_data):
            cue_loc = None
            for action, consq in stim['responses'].items():
                total = (consq['p_reward'] if 'p_reward' in consq else 0) + \
                        (consq['p_punish'] if 'p_punish' in consq else 0)
                if total > 1:
                    logger.error(f"Reward/Punish Percentage Exceed 1.0 for {action} in {stim['name']}")
                    raise
                if get_cues and ('p_reward' in consq):
                    cue_loc = peck_parse(action, 'l')
            if get_cues:
                self.cue_locations[stim['name']] = cue_loc
            playlist.append(np.repeat(i, stim['frequency']))

        logger.debug("Requesting stimuli directory change")
        params = await Request.spawn(request_type="SetParameters",
                                     component='audio-playback',
                                     body={'audio_dir': cf['stimulus_root']}
                                     )
        await params.send()
        dir_check = await Request.spawn(request_type="GetParameters",
                                        component='audio-playback',
                                        body=None,
                                        )
        # The following has a higher timeout due to the blocking action of stimuli import on decide-rs
        check_res = await dir_check.send(timeout=10000)
        if check_res.audio_dir != cf['stimulus_root']:
            logger.error(f"Auditory folder mismatch: got {check_res.audio_dir} expected {cf['stimulus_root']}")

        self.sample_rate = check_res.sample_rate
        self.playlist = np.array(playlist).flatten()
        if shuffle:
            np.random.shuffle(self.playlist)
        self.ptr = iter(self.playlist)
        self.replace = replace
        return self

    def next(self):
        if not self.replace:
            try:
                item = next(self.ptr)
            except StopIteration:
                if self.shuffle:
                    np.random.shuffle(self.playlist)
                self.ptr = iter(self.playlist)
                item = next(self.ptr)
        else:
            if self.shuffle:
                np.random.shuffle(self.playlist)
            self.ptr = iter(self.playlist)
            item = next(self.ptr)

        self.stimulus = self.stim_data[item]['name']
        return self.stim_data[item].copy()

    async def current_cue(self):
        if self.stimulus is None:
            logger.error("Trying to determine cue but no stimulus specified. Try initiating playlist first")
            raise
        return self.cue_locations[self.stimulus]

    async def play(self, stim=None):
        if stim is None:
            stim = self.stimulus
        logger.debug(f"Playback of {stim} requested")

        play_result = asyncio.create_task(
            catch('audio-playback',
                  caught=lambda msg: (msg.audio_id == stim) & (pub.playback == 1),
                  failure=lambda i: pub_err("audio-playback") if not i else None,
                  timeout=TIMEOUT)
        )
        req = await Request.spawn(request_type="ChangeState",
                                  component='audio-playback',
                                  body={'audio_id': stim, 'playback': 1}
                                  )
        await req.send()
        _, pub, _ = await play_result
        frame_count = pub.frame_count

        self.stim_duration = frame_count / self.sample_rate
        self.playing = True

        completion = asyncio.create_task(
            catch('audio-playback',
                  caught=lambda msg: (msg.playback == 0),
                  failure=lambda i: pub_err("audio-playback") if not i else None,
                  timeout=self.stim_duration + TIMEOUT)
        )
        return self.stim_duration, completion

    async def stop(self, context=None):
        pub_confirmation = asyncio.create_task(
            catch('audio-playback',
                  lambda msg: (msg.playback == 0),
                  failure=lambda i: pub_err("audio-playback") if not i else None,
                  timeout=100)
        )
        req = await Request.spawn(request_type="ChangeState",
                                  component='audio-playback',
                                  body={'playback': 0}
                                  )
        await req.send()
        await pub_confirmation
        self.playing = False
        return
