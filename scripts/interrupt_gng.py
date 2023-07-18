#!/usr/bin/python3
import os
import sys
sys.path.append(os.path.abspath(".."))
from lib.manipulate import *
from lib.inform import *
from google.protobuf.json_format import MessageToDict
import argparse
import asyncio
import logging
import random

__name__ = 'interrupt_gng'

p = argparse.ArgumentParser()
p.add_argument("user")
p.add_argument("birdID")
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


async def await_init():
    await_input = peck_parse(params['init_key'], 'r')

    def peck_init(key_state):
        pecked = MessageToDict(key_state,
                               preserving_proto_field_name=True)
        if (await_input in pecked) and (pecked[await_input]):
            return True
    await catch('peck-keys',
                caught=peck_init)


async def present_stim(pb, stim_data):
    dur, _ = pb.play(stim_data['name'])
    return dur


async def await_respond(pb, stim_data, duration):
    # await cue(pb.current_cue(), params['cue_color'])
    response = 'timeout'

    def resp_check(key_state):
        pecked = MessageToDict(key_state,
                               preserving_proto_field_name=True)
        for k, v in pecked.items():
            if v & (k in stim_data):
                pb.stop()
                return True
        return False

    responded, msg, rtime = await catch('peck-keys',
                                        caught=resp_check,
                                        timeout=duration or params['response_duration'])

    if not responded:
        return response, None
    else:
        for key, val in MessageToDict(msg, preserving_proto_field_name=True).items():
            if val & (key in stim_data):
                response = key
        return response, rtime


async def complete(playback, stim_data, response, rtime):
    # Determine outcome
    outcome = stim_data['responses'][response]
    rand = random.random()
    if outcome['reinforced']:
        if outcome['p_reward'] >= rand:
            await feed(params['feed_duration'], params['feed_delay'])
        result = 'feed'
    else:
        result = 'no_feed'
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
    await log_trial(msg=state.copy())
    # Advance
    stim_data = playback.next()
    return stim_data


async def main():
    context = zmq.Context()
    # Check status of decide-rs
    bg = asyncio.create_task(stayin_alive(address=IDENTITY, user=args.user))
    # Start logging
    await lincoln(log=f"{args.birdID}_{__name__}.log")
    logging.info("GNG.py initiated")

    light = await Sun.spawn(interval=300)
    asyncio.create_task(light.cycle())

    playback = await JukeBox.spawn(args.config,
                                   shuffle=True,
                                   replace=params['replace'])
    correction = 0
    stim_data = playback.next()

    await slack(f"GNG.py initiated on {IDENTITY}", usr=args.user)

    response = None
    while True:
        if response and (response == 'timeout'):
            await await_init()
        duration = await present_stim(playback, stim_data)
        response, rtime = await await_respond(playback, stim_data, duration)
        stim_data, correction = await complete(playback, stim_data, response, rtime)


if __name__ == "__gng__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("SIGINT Detected, shutting down.")
        asyncio.run(slack("PyCrust GNG is shutting down", usr=args.user))

