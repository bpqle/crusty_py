#!/usr/bin/python3
import os
import sys
sys.path.append(os.path.abspath(".."))
from lib.manipulate import *
from lib.inform import *
from google.protobuf.json_format import MessageToDict
import argparse
import asyncio
import time
import logging
import random

__exp__ = 'shape'

p = argparse.ArgumentParser()
p.add_argument("user")
p.add_argument("birdID")
p.add_argument("-F", "--ffoward", help="immediately skip to block 4", action='store_true')
p.add_argument("-B", "--block", help="skip to specific block", action='store', default=0)
p.add_argument("--color", help="set color of cues",
               choices=['blue', 'red', 'green'], default='blue')
p.add_argument('--init_position', help='key position to initiate trial',
               choices=['left', 'center', 'right'], default='center')
p.add_argument('--response_position', help="follow-up positions after initial peck",
               nargs='+', default=['left','right'])
p.add_argument("-T", "--trials", help="length of blocks 2-3", action='store', default=100)
p.add_argument('--feed_delay', help='time (in ms) to wait between response and feeding',
               action='store', default=0)
p.add_argument("--feed_duration", help="default feeding duration for correct responses (in ms)",
               action='store', default=4000)
p.add_argument("--response_duration", help="response window duration (in ms) in block 1",
               action='store', default=4000)
args = p.parse_args()

state = {
    'subject': args.birdID,  # logged
    'experiment': args.config,  # logged
    'name': __name__,  # logged
    'trial': 0,  # logged
    'block': 0,  # logged
}
params = {
    'user': args.user,
    'active': True,
    'response_duration': args.response_duration,
    'color': args.color,
    'block_length': args.trials,
    'init_position': args.init_position,
    'response_position': args.response_position or [args.init_position],
    'feed_delay': args.feed_delay,
    'feed_duration': args.feed_duration,
    'iti_min': 240  # with some variance
}


async def main():
    context = zmq.Context()
    bg = asyncio.create_task(stayin_alive(address=IDENTITY, user=args.user))

    await lincoln(log=f"{args.birdID}_{__name__}.log")
    logging.info("GNG.py initiated")

    light = await Sun.spawn(interval=300)
    asyncio.create_task(light.cycle())

    if (args.fforward) or (args.block == 4):
        state['block'] = 4
    else:
        state['block'] = args.block

    shaping = False
    while shaping:
        if not light.daytime:
            await asyncio.sleep(300)  # seconds
            continue
        if state['block'] == 0:
            await block0_feeder()
        elif state['block'] == 1:
            await block1_patience()
        elif state['block'] == 2:
            await block2_peck()
        elif state['block'] == 3:
            await block3_extend()
        elif state['block'] == 4:
            await block4_auton()
        else:
            raise RuntimeError(f"Bad shape block encountered {state['block']}")


async def block0_feeder():
    iti_var = 60
    iti = int(params['iti_min'] + random.random() * iti_var)

    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await feed(delay=params['feed_delay'])
    state.update({
        'trial': state.get('trial', 0) + 1,
    })
    logger.info(f"Trial {state['trial']} completed. Logging trial.")
    await log_trial(msg=state.copy())

    await asyncio.sleep(iti)
    if state['trial'] + 1 > params['block_length']:
        state.update({
            'trial': 0,
            'block': state.get('block', 0) + 1,
        })


async def block1_patience():
    iti_var = 60
    await_input = peck_parse(params['init_position'] ,'r')
    cue_pos = peck_parse(params['init_position'] ,'l')

    iti = int(params['iti_min'] + random.random() * iti_var)

    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await cue(cue_pos, params['cue_color'])

    def resp_check(key_state):
        pecked = MessageToDict(key_state,
                               preserving_proto_field_name=True)
        for k, v in pecked.items():
            if v & (k == await_input):
                return True
        return False

    responded, msg, rtime = await catch('peck-keys',
                                        caught=resp_check,
                                        timeout=params['response_duration'])

    # feed regardless of response
    await cue(cue_pos, 'off')
    await feed(delay=params['feed_delay'])

    if responded:
        logger.info("Bird pecked during block 1! Immediately advancing to block 2")
        state.update({
            'trial': state.get('trial', 0) + 1,
            'result': 'feed',
            'response': await_input,
            'rtime': rtime,
        })
    else:
        state.update({
            'trial': state.get('trial', 0) + 1,
            'result': 'feed',
            'response': 'timeout',
            'rtime': None,
        })

    logger.info(f"Trial {state['trial']} completed.")
    await log_trial(msg=state.copy())
    await asyncio.sleep(iti)

    if responded or (state['trial'] + 1 > params['block_length']):
        state.update({
            'trial': 0,
            'block': state.get('block', 0) + 1,
        })


async def block2_peck():
    iti_var = 15
    iti = int(random.random() * iti_var)
    await_input = peck_parse(params['init_position'], 'r')
    cue_pos = peck_parse(params['init_position'], 'l')

    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await cue(cue_pos, params['cue_color'])

    def resp_check(key_state):
        pecked = MessageToDict(key_state,
                               preserving_proto_field_name=True)
        for k, v in pecked.items():
            if v & (k == await_input):
                return True
        return False

    responded, msg, rtime = await catch('peck-keys',
                                        caught=resp_check,
                                        timeout=None)

    # feed regardless of response
    await cue(await_input, 'off')
    if responded:  # should always be True in this block
        await feed(delay=params['feed_delay'])
        state.update({
            'trial': state.get('trial', 0) + 1,
            'result': 'feed',
            'response': await_input,
            'rtime': rtime,
        })
        logger.info(f"Trial {state['trial']} completed.")
        await log_trial(msg=state.copy())
        await asyncio.sleep(iti)

        if state['trial'] + 1 > params['block_length']:
            state.update({
                'trial': 0,
                'block': state.get('block', 0) + 1,
            })
    else:
        raise Exception("Block 2 passed without any response!")

async def block3_extend():
    iti_var = 15
    iti = int(random.random() * iti_var)
    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await_input = peck_parse(params['init_position'] ,'r')
    cue_pos = peck_parse(params['init_position'] ,'l')
    await cue(cue_pos, params['cue_color'])
    def resp_check(key_state):
        pecked = MessageToDict(key_state,
                               preserving_proto_field_name=True)
        for k, v in pecked.items():
            if v & (k == await_input):
                return True
        return False
    await catch('peck-keys',
                caught=resp_check,
                timeout=None)
    await cue(cue_pos, 'off')

    cue2 = pick(params['response_position'])
    second_input = peck_parse(cue2, 'r')
    second_cue = peck_parse(cue2, 'l')
    await cue(second_cue, params['cue_color'])
    def resp_check(key_state):
        pecked = MessageToDict(key_state,
                               preserving_proto_field_name=True)
        for k, v in pecked.items():
            if v & (k == second_input):
                return True
        return False

    responded, msg, rtime = await catch('peck-keys',
                                        caught=resp_check,
                                        timeout=None)
    await cue(second_cue, 'off')

    await feed(delay=params['feed_delay'])

    state.update({
        'trial': state.get('trial', 0) + 1,
        'result': 'feed',
        'response': second_input,
        'rtime': rtime,
    })
    logger.info(f"Trial {state['trial']} completed.")
    await log_trial(msg=state.copy())
    await asyncio.sleep(iti)

    if state['trial'] + 1 > params['block_length']:
        state.update({
            'trial': 0,
            'block': state.get('block', 0) + 1,
        })


async def block4_auton():
    iti_var = 15
    iti = int(random.random() * iti_var)
    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await_input = peck_parse(params['init_position'], 'r')
    def resp_check(key_state):
        pecked = MessageToDict(key_state,
                               preserving_proto_field_name=True)
        for k, v in pecked.items():
            if v & (k == await_input):
                return True
        return False
    await catch('peck-keys',
                caught=resp_check,
                timeout=None)

    cue2 = pick(params['response_position'])
    second_input = peck_parse(cue2, 'r')
    def resp_check(key_state):
        pecked = MessageToDict(key_state,
                               preserving_proto_field_name=True)
        for k, v in pecked.items():
            if v & (k == second_input):
                return True
        return False

    responded, msg, rtime = await catch('peck-keys',
                                        caught=resp_check,
                                        timeout=None)

    await feed(delay=params['feed_delay'])

    state.update({
        'trial': state.get('trial', 0) + 1,
        'result': 'feed',
        'response': second_input,
        'rtime': rtime,
    })
    logger.info(f"Trial {state['trial']} completed.")
    await log_trial(msg=state.copy())
    await asyncio.sleep(iti)

    if state['trial'] == params['block_length']:
        await slack(f"Interrupt Shape completed for {state['subject']}. Trials will continue running",
                    usr=params['user'])
        logger.info('Shape completed')


def pick(group):
    return group[int(random.random() // (1/len(group)))]


if __exp__ == 'shape':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("SIGINT Detected, shutting down.")
        asyncio.run(slack("PyCrust GNG is shutting down", usr=args.user))