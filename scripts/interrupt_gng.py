#!/usr/bin/python3
import os
import sys

sys.path.append(os.path.abspath(".."))
from lib.process import *
from lib.inform import *
import argparse
import asyncio
import logging
import random

__name__ = 'interrupt-gng'

p = argparse.ArgumentParser()
p.add_argument("birdID")
p.add_argument("user")
p.add_argument("config")
p.add_argument("--response_duration", help="response window duration (in ms)",
               action='store', default=6000)
p.add_argument("--feed_duration", help="default feeding duration for correct responses (in ms)",
               action='store', default=4000)
p.add_argument('--replace', help="randomize trials with replacement", action='store_true')
p.add_argument('--feed_delay', help='time (in ms) to wait between response and feeding',
               action='store', default=0)
p.add_argument('--init_position', help='key position to initiate trial',
               choices=['left', 'center', 'right'], default='center')
p.add_argument('--log_level', default='INFO')
args = p.parse_args()

state = {
    'subject': args.birdID,  # logged
    'experiment': args.config,  # logged
    'name': __name__,  # logged
    'trial': 0,  # logged
    'result': None,  # logged
    'reinforced': False,  # logged
    'response': None,  # logged
    'rtime': None,  # logged
    'stimulus': None,  # logged
}

params = {
    'user': args.user,
    'active': True,
    'response_duration': args.response_duration,
    'feed_duration': args.feed_duration,
    'replace': args.replace,
    'feed_delay': args.feed_delay,
    'min_iti': 15,
    'init_key': args.init_position,
}
lincoln(log=f"{args.birdID}_{__name__}.log", level=args.log_level)
logger = logging.getLogger('main')


async def await_init():
    await_input = peck_parse(params['init_key'], 'r')

    def peck_init(key_state):
        if (await_input in key_state) and (key_state[await_input]):
            return True

    await decider.scry(
        'peck-keys',
        condition=peck_init,
    )


async def present_stim(stim_data):
    dur, _ = decider.play(stim_data['name'])
    return dur


async def await_respond(stim_data, duration):
    # await cue(pb.current_cue(), params['cue_color'])
    response = 'timeout'

    def resp_check(key_state):
        nonlocal response
        for k, v in key_state.items():
            if v & (k in stim_data):
                asyncio.create_task(decider.stop())
                response = k
                return True
        return False

    responded, msg, rtime = await decider.scry('peck-keys',
                                               condition=resp_check,
                                               timeout=duration or params['response_duration'])

    if not responded:
        return response, None
    else:
        return response, rtime


async def complete(stim_data, response, rtime):
    # Determine outcome
    outcome = stim_data['responses'][response]
    rand = random.random()
    result = 'no_feed'
    if outcome['reinforced']:
        if outcome['p_reward'] >= rand:
            await decider.feed(params['feed_delay'])
            result = 'feed'
    # Log Trial
    state.update({
        'trial': state.get('trial', 0) + 1,
        'result': result,
        'response': response,
        'rtime': rtime,
        'reinforced': outcome['reinforced'],
        'stimulus': stim_data['name']
    })
    logger.info(f"Trial {state['trial']} completed. Logging trial.")
    await post_host(msg=state.copy(), target='trials')
    # Advance
    stim_data = decider.playback.next()
    return stim_data


async def main():
    # Start logging
    global decider
    decider = Morgoth()
    await contact_host()
    asyncio.create_task(decider.messenger.eye())

    await decider.set_light()
    await decider.set_feeder(duration=params['feed_duration'])
    await decider.init_playback(args.config, replace=args.replace)
    asyncio.create_task(decider.light_cycle())
    stim_data = decider.playback.next()

    logger.info("interrupt_gng.py initiated")
    await slack(f"interrupt_gng.py initiated on {IDENTITY}", usr=args.user)

    response = None
    while True:
        if response and (response == 'timeout'):
            await await_init()
        duration = await present_stim(stim_data)
        response, rtime = await await_respond(stim_data, duration)
        stim_data, correction = await complete(stim_data, response, rtime)


if __name__ == "interrupt-gng":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("SIGINT Detected, shutting down.")
        asyncio.run(slack("PyCrust GNG is shutting down", usr=args.user))
