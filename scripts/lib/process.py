import json
import numpy as np
import zmq.asyncio

from .inform import *
from .decrypt import Component
from .errata import pub_err, state_err
from .dispatch import Sauron
from google.protobuf.json_format import MessageToDict
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
        logger.state("Apparatus initiated.")

    async def scry(self, components, components=None, condition, failure=None, timeout=None):
        """
        Search for incoming messages matching component name and test for specific condition
        Optional failure and timeout.
        :param components: str or list, name(s) of decide-core component
        :param condition: fn, test the dict-type message emmited from core
        :param failure: fn, optional error/failure state, only in conjunction with timeout
        :param timeout: time(ms) to await and test messages.
        :return:
        """
        interrupted = False
        message = None
        timer = None
        if isinstance(components, str):
            topic = "state/" + components
            self.messenger.scryer.subscribe(topic.encode("utf-8"))
            components = [components]
        elif isinstance(components, list):
            for c in components:
                topic = "state/" + c
                self.messenger.scryer.subscribe(topic.encode("utf-8"))
        else:
            raise ValueError("Invalid arguments for scry: no component or components specified.")

        async def test(func):
            nonlocal interrupted, message, start, timer, end
            while True:
                *topic, msg = await self.messenger.scryer.recv_multipart()
                state, comp = topic[0].decode("utf-8").split("/")
                proto_comp = Component(state, comp)
                _timestamp, state_msg = await proto_comp.from_pub(msg)
                decoded = MessageToDict(state_msg,
                                        including_default_value_fields=True,
                                        preserving_proto_field_name=True)
                logger.state(f"Scry {components} - found item in queue from {comp}")
                if func(decoded) is True:
                    end = time.time()
                    timer = end - start
                    message = decoded
                    interrupted = True
                    logger.debug(f"Scry {components} - check succeeded. Ending.")
                    return
                else:
                    logger.debug(f"Scry {components} - check failed. Continuing.")
                    continue

        logger.state(f"Scry process started for {components}, purging queue")
        start = time.time()
        if timeout is not None:
            # Sanity check: everything from miliseconds to seconds
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
                    failure(components)
        else:
            await test(condition)

        logger.state(f"Scry finished for {components}. Unsubscribing from all topics")
        for c in components:
            topic = "state/" + c
            self.messenger.scryer.unsubscribe(topic.encode("utf-8"))
        return comp, interrupted, message, timer

    async def set_feeder(self, duration):
        """
        Configure food motor
        :param duration: duration (ms) to automatically run motor
        :return:
        """
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
        global FEED_TIME
        FEED_TIME = duration

    async def set_light(self, interval=300000):
        """
        Configure house light duration
        :param interval: duration (ms) to update house light
        :return:
        """
        if interval > 1000:
            interval = int(interval / 1000)
        self.sun = Sun(interval)
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
        """

        :param cfg: full path to JSON config file
        :param shuffle: bool, defaults to True, shuffle playlist in config file
        :param replace: bool, defaults to True, pull from entire playlist every iteration
        :param get_cues: bool, defaults to True, infer correct corresponding LED cue light.
        :return:
        """
        self.playback = await JukeBox.spawn(cfg, shuffle, replace, get_cues)
        logger.state("Requesting stimuli directory change")
        await self.messenger.command(
            request_type="SetParameters",
            component='audio-playback',
            body={'audio_dir': self.playback.dir}
        )
        # GetParams only used here to acquire configured sample rate.
        # Can't get the new audio directory requested immediately since the import action on 
        # decide-core is non-blocking. We won't know when it's completed
        dir_check = await self.messenger.command(
            request_type="GetParameters",
            component='audio-playback',
            body=None,
            timeout=None
        )
        # if dir_check['audio_dir'] != self.playback.dir:
        #     logger.error(f"Auditory folder mismatch: got {dir_check['audio_dir']} expected {self.playback.dir}")

        self.playback.sample_rate = dir_check['sample_rate']
        logger.state(f"Got sampling rate {dir_check['sample_rate']}")

    async def feed(self, delay=0):
        """
        Automcatically run food motor and await end
        :param delay: duration (ms) to wait before running motor
        :return:
        """
        logger.state('Feed requested')
        await asyncio.sleep(delay)
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component='stepper-motor',
            body={'running': True, 'direction': True}
        ))
        a = asyncio.create_task(self.scry(
            'stepper-motor',
            condition=lambda pub: pub['running'] is True,
            failure=pub_err,
            timeout=TIMEOUT
        ))
        await asyncio.gather(a, b)
        logger.state('feeding confirmed by decide-rs, awaiting motor stop')
        await self.scry(
            'stepper-motor',
            condition=lambda pub: not pub['running'],
            failure=pub_err,
            timeout=FEED_TIME + TIMEOUT
        )
        logger.state('motor stop confirmed by decide-rs')
        return

    async def cue(self, loc, color):
        """
        Activate led at specific location
        :param loc: str, location. Input string will be checked by "peck_parse()"
        :param color: ['red','blue','green','all','off']
        :return:
        """
        pos = peck_parse(loc, mode='l')
        logger.state(f'Requesting cue {pos}')
        a = asyncio.create_task(self.scry(
            pos,
            condition=lambda pub: pub['led_state'] == color,
            failure=pub_err,
            timeout=TIMEOUT
        ))
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component=pos,
            body={'led_state': color}
        ))
        await asyncio.gather(a, b)
        return

    async def cues_off(self):
        """
        Sets all LED cues to off
        :return:
        """
        for pos in ['peck-leds-left', 'peck-leds-right', 'peck-leds-center']:
            await self.cue(pos, 'off')

    async def light_cycle(self):
        """
        This function will await messages regarding light cycle update
        Should be run within a create_task() or gather() and not blocking-awaited
        """
        timeout = self.sun.interval + 10  # give an extra 10 seconds
        try:
            while True:
                decoded = await asyncio.wait_for(self.messenger.light_q.get(), timeout=timeout)  # timeout in seconds
                self.sun.update(decoded)
                logger.state("House-light state updated")
        except asyncio.TimeoutError:
            raise state_err(f"No house light updates received in {timeout}s. Decide-rs may be down")
        except asyncio.CancelledError:
            logger.warning("Light Cycle has been cancelled due to another task's failure.")

    async def blip(self, duration, brightness=0):
        """
        Turn off house lights for duration. Alternatively, set houselight to specific level.
        :param duration:
        :param brightness: optional, defaults to 0
        :return:
        """
        logger.state("Manually changing house lights")
        a = asyncio.create_task(self.scry(
            'house-light',
            condition=lambda pub: (pub['manual']) and (pub['brightness'] == brightness),
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
            condition=lambda pub: not pub['manual'],
            failure=pub_err,
        ))
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component='house-light',
            body={'manual': False, 'dyson': True}
        ))
        await asyncio.gather(a, b)
        logger.state("Returning house lights to cycle succeeded")

    async def play(self, stim=None, poll_end=True):
        """
        play specified stimuli, or last played stimuli if not specified.
        Automatically awaits the stimuli end message, but can be ignored for interruption.
        :param stim: name of stimuli, to be used in conjunction with playback's iterator.
        :param poll_end: True to return after stimuli end, False to return as soon as stimuli starts
        :return:
        """
        if stim is None:
            stim = self.playback.stimulus
        logger.state(f"Playback of {stim} requested")
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component='audio-playback',
            body={'audio_id': stim, 'playback': True}
        ))
        a = asyncio.create_task(self.scry(
            'audio-playback',
            condition=lambda msg: ('audio_id' in msg)
                                  and ('playback' in msg)
                                  and (msg['audio_id'] == stim)
                                  and (msg['playback']),
            failure=pub_err,
            timeout=TIMEOUT
        ))
        await b
        _, _, pub, _ = await a

        frame_count = pub['frame_count']
        stim_duration = frame_count / self.playback.sample_rate
        self.playback.duration = stim_duration
        if poll_end:
            await asyncio.create_task(self.scry(
                'audio-playback',
                condition=lambda msg: ('playback' in msg) and (msg['playback'] is False),
                failure=pub_err,
                timeout=stim_duration * 1000 + TIMEOUT
            ))
        else:
            return

    async def stop(self):
        """
        Request stimuli stop
        :return:
        """
        logger.state("Requesting playback stop.")
        a = asyncio.create_task(self.scry(
            'audio-playback',
            condition=lambda msg: ('playback' in msg) and (msg['playback'] is False),
            failure=pub_err,
            timeout=TIMEOUT
        ))
        b = asyncio.create_task(self.messenger.command(
            request_type="ChangeState",
            component='audio-playback',
            body={'playback': 0}
        ))
        await asyncio.gather(a, b)
        return


class Sun:
    def __init__(self, interval):
        self.manual = False
        self.dyson = True
        self.brightness = 0
        self.daytime = True
        self.interval = interval

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
