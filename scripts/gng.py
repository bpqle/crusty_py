#!/usr/bin/python3
import os
import sys
sys.path.append(os.path.abspath(".."))
from lib.engine import *
from lib.inform import *
from google.protobuf.json_format import MessageToDict
import argparse
import asyncio
import time
import logging
import random

__exp__ = 'gng'

p = argparse.ArgumentParser()
p.add_argument("user")
p.add_argument("birdID")
p.add_argument("config")
p.add_argument("--response_duration", help="response window duration (in ms)",
               action='store', default=4000)
p.add_argument("--feed_duration", help="default feeding duration for correct responses (in ms)",
               action='store', default=4000)
p.add_argument('--max_corrections', help="maximum number of correction trials (0 = no corrections)",
               action='store', default=10)
p.add_argument('--replace', help="randomize trials with replacement", action='store_true')
p.add_argument('--correction_timeout', help="correction trials for incorrect failure to respond", action='store_true')
p.add_argument('--lightsout_duration', help="default lights out duration for incorrect responses (in ms)",
               action='store', default=10000)
p.add_argument('--cue_frequency', help="frequency to display cue lights for correction trials",
               choices=['always', 'sometimes', 'never'], default='never')
p.add_argument('--cue_color', help="color of cue lights for correction trials",
               choices=['red', 'blue', 'green', 'white'], default='blue')
p.add_argument('--feed_delay', help='time (in ms) to wait between response and feeding',
               action='store', default=0)
p.add_argument('--init_position', help='key position to initiate trial',
               choices=['left', 'center', 'right'], default='center')
args = p.parse_args()


state = {
    'trial': 0,  # logged
    'result': None,  # logged
    'correct': False,  # logged
    'response': None,  # logged
    'rtime': None,  # logged
    'correction': 0,  # logged
    'stimulus': None,  # logged
}
params = {
    'subject': args.birdID,  # logged
    'user': args.user,
    'experiment': args.config,  # logged
    'name': __exp__,  # logged
    'active': True,
    'resp_window': args.response_duration,
    'feed_duration': args.feed_duration,
    'punish_duration': args.lightsout_duration,
    'max_corrections': args.max_corrections,
    'rand_replace': args.replace,
    'correction_timeout': args.correction_timeout,
    'cue_frequency': args.cue_frequency,
    'cue_color': args.cue_color,
    'feed_delay': args.feed_delay,
    'min_iti': 100,
    'init_key': f"peck_{args.init_position}",
}


async def await_init():

    def peck_init(key_state):
        pecked = MessageToDict(key_state,
                               preserving_proto_field_name=True)
        if (params['init_key'] in pecked) and (pecked[params['init_key']]):
            return True
    await catch('peck-keys',
                caught=peck_init)


async def present_stim(pb, stim_data):
    await pb.play(stim_data['name'])


async def await_respond(pb, stim_data, correction):
    if correction and await correction_check(correction):
        await cue(pb.current_cue(), params['cue_color'])
    response = 'timeout'

    def resp_check(key_state):
        pecked = key_state.to_dict()
        for k, v in pecked.items():
            if v & (k in stim_data):
                return True
        return False

    responded, msg, rtime = await catch('peck-keys',
                                        caught=resp_check,
                                        timeout=params['response-window'])
    if not responded:
        return response, None
    else:
        for key, val in msg.to_dict().items():
            if val & (key in stim_data):
                response = key
        return response, rtime


async def complete(stim_data, correction, stim, response, rtime):
    # Determine outcome
    outcome = stim_data['response'][response]
    rand = random.random()
    if outcome['correct']:
        if outcome['p_reward'] >= rand:
            await asyncio.sleep(params['feed_delay'])
            await feed(params['feed_duration'])
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
        'rtime': rtime,
        'correct': outcome['correct'],
        'correction': state.get('correction'),
        'stimulus': stim_data['name']
    })
    logger.info(state)
    # Advance
    if (response == 'timeout') & params['correction_timeout']:
        logger.debug("Response timeout, next trial is correction trial.")
    elif (response != 'timeout') & (not outcome['correct']) & (correction < params['max_corrections']):
        correction += 1
        logger.debug("Next Trial correction.")
    else:
        correction = 0
        stim_data = next(stim).copy()
    return stim_data, correction


async def correction_check(correction):
    if params['cue_frequency'] == 'never':
        return False
    elif params['cue_frequency'] == 'always':
        return True
    elif params['cue_frequency'] == 'sometimes':
        return np.exp(correction / params['max_corrections']) >= random.random()


async def main():
    context = zmq.Context()
    await lincoln(log=f"{args.birdID}_{__exp__}.log")
    logging.info("GNG.py initiated")

    light = await Sun.spawn(interval=300)
    lightyear = asyncio.create_task(light.cycle())

    pb = await JukeBox.spawn(args.config)
    stim = iter(pb)
    correction = 0
    stim_data = next(stim).copy()

    await slack(f"GNG.py initiated on {HOSTNAME}", usr=args.user)

    while True:
        await await_init()
        await present_stim(pb, stim_data)
        response, rtime = await await_respond(pb, stim_data, correction)
        stim_data, correction = await complete(stim_data, correction, stim, response, rtime)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("SIGINT Detected, shutting down.")
        asyncio.run(slack("PyCrust GNG is shutting down", usr=args.user))

