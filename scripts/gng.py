import sys
import os
import argparse
import asyncio
import time
import logging
import random
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))
sys.path.insert(1, libpath)

from lib.control import *
from lib.compose import *
from lib.connect import *

p = argparse.ArgumentParser()
p.add_argument("user")
p.add_argument("birdID")
p.add_argument("config")
p.add_argument("--response-duration", help="response window duration (in ms)",
               action='store_const', default=4000)
p.add_argument("--feed-duration", help="default feeding duration for correct responses (in ms)",
               action='store_const', default=4000)
p.add_argument('--max-corrections', help="maximum number of correction trials (0 = no corrections)",
               action='store_const', default=10)
p.add_argument('--replace', help="randomize trials with replacement", action='store_true')
p.add_argument('--correction-timeout', help="correction trials for incorrect failure to respond", action='store_true')
p.add_argument('--lightsout-duration', help="default lights out duration for incorrect responses (in ms)",
               action='store_const', default=10000)
p.add_argument('--cue-frequency', help="frequency to display cue lights for correction trials",
               choices=['always', 'sometimes', 'never'], default='never')
p.add_argument('--cue-color', help="color of cue lights for correction trials",
               choices=['red', 'blue', 'green', 'white'], default='blue')
p.add_argument('--feed-delay', help='time (in ms) to wait between response and feeding',
               action='store_const', default=0)
p.add_argument('--init-position', help='key position to initiate trial',
               choices=['left', 'center', 'right'])
args = p.parse_args()


state = {
    'trial': 0,
    'phase': None,
    'result': None,
    'correct': False,
    'response': None,
    'correction': 0,
    'stimulus': None,
}
params = {
    'subject': args['birdID'],
    'user': args['user'],
    'active': True,
    'resp_window': args['response-duration'],
    'feed_duration': args['feed-duration'],
    'punish_duration': args['lightsout-duration'],
    'max_corrections': args['max-corrections'],
    'rand_replace': args['replace'],
    'correction_timeout': args['correction-timeout'],
    'cue_frequency': args['cue-frequency'],
    'cue_color': args['cue-color'],
    'feed_delay': args['feed-delay'],
    'min_iti': 100,
    'init_key': args['init-position'],
}
lights = Sun(interval=300)
pb = PlayBack(args['config'])
stim = iter(pb)
correction = 0
stim_data = next(stim).copy()


def await_init():
    def peck_init(key_state):
        pecked = key_state.to_dict()
        if pecked[params['init_key']]:
            return True
    await catch('peck-keys', peck_init, present_stim)


def present_stim():
    play_handle = pb.play(stim_data['name'])
    await play_handle
    await_respond()


def await_respond():
    if correction & correction_check():
        cue(pb.current_cue(), params['cue_color'])
    response = 'timeout'

    def resp_check(key_state):
        nonlocal response
        pecked = key_state.to_dict()
        for key, val in pecked.items():
            if val & (key in stim_data):
                response = key
                return True
        return False

    await catch('peck-keys', resp_check, complete,
                timeout=params['response-window'],
                response=response)


def complete(**kwargs):
    response = kwargs['response']
    rtime = kwargs['timer']
    global stim_data
    global correction
    # Determine outcome
    outcome = stim_data['response'][response]
    rand = random.random()
    if outcome['correct']:
        if outcome['p_reward'] >= rand:
            await asyncio.sleep(params['feed_delay'])
            feed(params['feed_duration'])
        result = 'feed'
    else:
        if outcome['p_punish'] >= rand:
            await blip(0, params['punish_duration'])
        result = 'no_feed'
    # Log Trial
    state.update({
        'trial': state.get('trial', 0) + 1,
        'result': result,
        'response': response,
        'correct': outcome['correct'],
        'correction': correction,
        'stimulus': stim_data['name']
    })
    logger.info()
    # Advance
    if (response == 'timeout') & params['correction_timeout']:
        logger.debug("Response timeout, next trial is correction trial.")
    elif (response != 'timeout') & (not outcome['correct']) & (correction < params['max_corrections']):
        correction += 1
        logger.debug("Next Trial correction.")
    else:
        correction = 0
        stim_data = next(stim).copy()
    await_init()


def correction_check():
    if params['cue_frequency'] == 'never':
        return False
    elif params['cue_frequency'] == 'always':
        return True
    elif params['cue_frequency'] == 'sometimes':
        return np.exp(correction / params['max_corrections']) >= random.random()


if __name__ == '__main__':
    asyncio.run(lights.cycle())
    await_init()
