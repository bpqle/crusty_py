import json
import numpy as np
import zmq.asyncio

from .errata import pub_err
from .dispatch import Sauron
from .inform import *
import asyncio
import logging

logger = logging.getLogger('main')


class Morgoth:
    def __init__(self, messenger=None):
        self.messenger = None
        self.sun = None
        self.playback = None
        if isinstance(messenger, Sauron):
            self.messenger = messenger
        else:
            self.messenger = Sauron()
        logger.state("Apparatus-class Object created. Praise Dan.")

    async def scry(self, component, condition, failure=None, timeout=None):
        logger.state(f"Scry process started for {component}, purging queue")
        interrupted = False
        message = None
        timer = None

        async def test(func):
            nonlocal interrupted, message, start, timer, end
            while True:
                logger.state(f"Scry {component} - test found message in queue")
                comp, state = await self.messenger.queue.get()
                if (comp == component) & func(state):
                    end = time.time()
                    timer = end - start
                    message = state
                    interrupted = True
                    logger.debug(f"Scry {component} - check succeeded. Ending.")
                    # self.messenger.queue.task_done()
                    return
                else:
                    logger.debug(f"Scry {component} - check failed. Continuing.")
                    # self.messenger.queue.task_done()
                    if comp != component:
                        await self.messenger.queue.put([comp, state])
                    await asyncio.sleep(0.001)
                    continue

        start = time.time()
        if timeout is not None:
            timeout = timeout / 1000 if timeout > 20 else timeout
            try:
                await asyncio.wait_for(test(condition), timeout)
            except asyncio.exceptions.TimeoutError:
                message = None
                timer = timeout
                if failure is not None:
                    end = time.time()
                    timer = end - start
                    logger.error(f"Required response not received within timeout {timeout},"
                                 f" time elapsed is {timer}")
                    failure(component)
        else:
            await test(condition)

        logger.state(f"Scry finished for {component}.")
        return interrupted, message, timer

    async def set_feeder(self, duration):
        logger.state("Setting feed duration")
        await self.messenger.command(request_type="SetParameters",
                                     component='stepper-motor',
                                     body={'timeout': duration}
                                     )

        interval_check = await self.messenger.command(request_type="GetParameters",
                                                      component='stepper-motor',
                                                      body=None)
        if int(interval_check['timeout']) != duration:
            logger.error(f"Stepper motor timeout parameter not set to {duration}")

    async def set_light(self, interval=300):
        self.sun = Sun()
        await self.messenger.command(request_type="SetParameters",
                                     component='house-light',
                                     body={'clock_interval': interval})
        interval_check = await self.messenger.command(request_type="GetParameters",
                                                      component='house-light',
                                                      body=None)
        if int(interval_check['clock_interval']) != interval:
            logger.error(f"House-Light Clock Interval not set to {interval},"
                         f" got {interval_check['clock_interval']}")

    async def init_playback(self, cfg, shuffle=True, replace=False, get_cues=True):
        self.playback = await JukeBox.spawn(cfg, shuffle, replace, get_cues)
        logger.state("Requesting stimuli directory change")
        await self.messenger.command(
            request_type="SetParameters",
            component='audio-playback',
            body={'audio_dir': self.playback.dir}
        )
        # The following has a higher timeout due to the blocking action of stimuli import on decide-rs
        dir_check = await self.messenger.command(
            request_type="GetParameters",
            component='audio-playback',
            body=None,
            timeout=100000
        )
        # if dir_check['audio_dir'] != self.playback.dir:
        #     logger.error(f"Auditory folder mismatch: got {dir_check['audio_dir']} expected {self.playback.dir}")

        self.playback.sample_rate = dir_check['sample_rate']
        logger.state(f"Got sampling rate {dir_check['sample_rate']}")

    async def feed(self, delay=0):
        logger.state('Feed requested')
        await asyncio.sleep(delay)
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component='stepper-motor',
            body={'running': True, 'direction': True}
        ))
        a = asyncio.create_task(self.scry(
            'stepper-motor',
            condition=lambda pub: ('running' in pub) and (pub['running']),
            failure=pub_err,
            timeout=TIMEOUT
        ))
        await asyncio.gather(a, b)
        logger.state('feeding confirmed by decide-rs, awaiting motor stop')
        await self.scry(
            'stepper-motor',
            condition=lambda pub: ('running' in pub) and (not pub['running']),
            failure=pub_err,
            timeout=8000
        )
        logger.state('motor stop confirmed by decide-rs')
        await self.messenger.purge()
        return

    async def cue(self, loc, color):
        pos = peck_parse(loc, mode='l')
        logger.state(f'Requesting cue {pos}')
        a = asyncio.create_task(self.scry(
            pos,
            condition=lambda pub: ('led_state' in pub) and (pub['led_state'] == color),
            failure=pub_err,
            timeout=TIMEOUT
        ))
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component=pos,
            body={'led_state': color}
        ))
        await asyncio.gather(a, b)
        await self.messenger.purge()
        return

    async def cues_off(self):
        for pos in ['peck-leds-left', 'peck-leds-right', 'peck-leds-center']:
            await self.cue(pos, 'off')

    async def light_cycle(self):
        while True:
            decoded = await self.messenger.light_q.get()
            self.sun.update(decoded)
            logger.state("House-light state updated")

    async def blip(self, duration, brightness=0):
        logger.state("Manually changing house lights")
        a = asyncio.create_task(self.scry(
            'house-light',
            condition=lambda pub: True if ('brightness' in pub) and (pub['brightness'] == brightness) else False,
            failure=pub_err,
            timeout=TIMEOUT
        ))

        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component='house-light',
            body={'manual': True, 'brightness': brightness}
        ))
        await asyncio.gather(a, b)
        logger.state("Manually changing house lights confirmed by decide-rs.")

        await asyncio.sleep(duration / 1000)

        logger.state("Returning house lights to cycle")
        a = asyncio.create_task(self.scry(
            'house-light',
            condition=lambda pub: ('manual' in pub) and (not pub['manual']),
            failure=pub_err,
        ))
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component='house-light',
            body={'manual': False, 'dyson': True}
        ))
        await asyncio.gather(a, b)
        await self.messenger.purge()
        logger.state("Returning house lights to cycle succeeded")

    async def play(self, stim=None):
        if stim is None:
            stim = self.playback.stimulus
        logger.state(f"Playback of {stim} requested")
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component='audio-playback',
            body={'audio_id': stim, 'playback': 1}
        ))
        a = asyncio.create_task(self.scry(
            'audio-playback',
            condition=lambda msg: ('audio_id' in msg)
                                  and ('playback' in msg)
                                  and (msg['audio_id'] == stim)
                                  and (msg['playback'] == 1),
            failure=pub_err,
            timeout=TIMEOUT
        ))
        await b
        _, pub, _ = await a

        frame_count = pub['frame_count']
        stim_duration = frame_count / self.playback.sample_rate
        self.playback.duration = stim_duration

        handle = asyncio.create_task(self.scry(
            'audio-playback',
            condition=lambda msg: ('playback' in msg) and (msg['playback'] == 0),
            failure=pub_err,
            timeout=stim_duration * 1000 + TIMEOUT
        ))
        await handle

    async def stop(self):
        logger.state("Requesting playback stop.")
        a = asyncio.create_task(self.scry(
            'audio-playback',
            condition=lambda msg: ('playback' in msg) and (msg['playback'] == 0),
            failure=pub_err,
            timeout=TIMEOUT
        ))
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component='audio-playback',
            body={'playback': 0}
        ))
        await b
        await a
        await self.messenger.purge()
        return


class Sun:
    def __init__(self):
        self.manual = False
        self.dyson = True
        self.brightness = 0
        self.daytime = True

    def update(self, decoded):
        logger.state("Updating House-Light from PUB")
        for key, val in decoded.items():
            setattr(self, key, val)
        return True


class JukeBox:
    def __init__(self):
        self.stimulus = None
        self.stim_data = None
        self.sample_rate = None
        self.ptr = None
        self.shuffle = True
        self.replace = False
        self.playlist = None
        self.dir = None
        self.cue_locations = None
        self.duration = None

    @classmethod
    async def spawn(cls, cfg, shuffle=True, replace=False, get_cues=True):
        logger.info("Spawning Playback Machine")
        self = JukeBox()
        with open(cfg) as file:
            cf = json.load(file)
            self.dir = cf['stimulus_root']
            self.stim_data = cf['stimuli']

        self.cue_locations = {}
        playlist = np.empty(shape=0)

        logger.state("Validating and generating playlist")
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
            added = np.repeat(i, stim['frequency'])
            playlist = np.append(playlist, added)

        assert (playlist.ndim == 1)
        logger.info(f"Playlist {playlist}")
        self.playlist = playlist
        if shuffle:
            np.random.shuffle(self.playlist)
        self.ptr = iter(self.playlist)
        self.replace = replace
        return self

    def next(self):
        if not self.replace:
            try:
                item = int(next(self.ptr))
            except StopIteration:
                if self.shuffle:
                    np.random.shuffle(self.playlist)
                self.ptr = iter(self.playlist)
                item = int(next(self.ptr))
        else:
            if self.shuffle:
                np.random.shuffle(self.playlist)
            self.ptr = iter(self.playlist)
            item = next(self.ptr)

        self.stimulus = self.stim_data[item]['name']
        return self.stim_data[item].copy()

    def current_cue(self):
        if self.stimulus is None:
            logger.error("Trying to determine cue but no stimulus specified. Try initiating playlist first")
            raise
        return self.cue_locations[self.stimulus]


# This function maintains sanity
def peck_parse(phrase, mode):
    """
    Takes in a string containing location (left, right, center)
     and outputs a string that matches the method to be used
    :param phrase: string variable to be parsed
    :param mode: 'l' for led, 'r' for key/response
    :return:
    """
    if mode in ['led', 'l', 'leds']:
        if 'left' in phrase:
            return 'peck-leds-left'
        elif 'right' in phrase:
            return 'peck-leds-right'
        elif 'center' in phrase:
            return 'peck-leds-center'
    elif mode in ['response', 'r']:
        if 'left' in phrase:
            return 'peck_left'
        elif 'right' in phrase:
            return 'peck_right'
        elif 'center' in phrase:
            return 'peck_center'
