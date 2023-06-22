import sys
import os
import argparse
import asyncio
import time
import logging
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))
sys.path.insert(1, libpath)

from lib.interact import *
from lib.utils import *
from lib.connect import *
from lib.components import Component


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
               choices=['always','sometimes','never'], default='never')
p.add_argument('--cue-color', help="color of cue lights for correction trials",
               choices=['red','blue','green','white'], default='blue')
p.add_argument('--feed-delay', help='time (in ms) to wait between response and feeding',
               action='store_const', default=0)
p.add_argument('--init-position', help='key position to initiate trial',
               choices=['left','center','right'])
args = p.parse_args()


state = {
    'trial': 0,
    'phase': None,
    'result': None,
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

pb = PlayBack(args['config'])
stim = iter(pb)


def await_init():
    def peck_init(key_state):
        pecked = key_state.to_dict()
        if pecked[params['init_key']]:
            return True
    catch('peck-keys', peck_init, present_stim)


def present_stim():
    stim_data = next(stim)
    play_handle = pb.play()

if __name__ == '__main__':
    await_init()