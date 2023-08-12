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

__name__ = 'shape'

p = argparse.ArgumentParser()
p.add_argument("birdID")
p.add_argument("user")
p.add_argument("-F", "--fforward", help="immediately skip to block 4", action='store_true')
p.add_argument("-B", "--block", help="skip to specific block", action='store', default=0)
p.add_argument("--color", help="set color of cues",
               choices=['blue', 'red', 'green'], default='blue')
p.add_argument('--init_position', help='key position to initiate trial',
               choices=['left', 'center', 'right'], default='center')
p.add_argument('--response_position', help="follow-up positions after initial peck",
               nargs='+', default=['left', 'right'])
p.add_argument("-T", "--trials", help="length of blocks 2-3", action='store', default=100)
p.add_argument('--feed_delay', help='time (in ms) to wait between response and feeding',
               action='store', default=0)
p.add_argument("--feed_duration", help="default feeding duration for correct responses (in ms)",
               action='store', default=4000)
p.add_argument("--response_duration", help="response window duration (in ms) in block 1",
               action='store', default=4000)
p.add_argument('--log_level', default='INFO')
args = p.parse_args()

state = {
    'subject': args.birdID,  # logged
    'name': __name__,  # logged
    'trial': 0,  # logged
    'block': 0,  # logged
}
params = {
    'user': args.user,
    'active': True,
    'response_duration': args.response_duration,
    'cue_color': args.color,
    'block_length': int(args.trials),
    'init_position': args.init_position,
    'response_position': args.response_position or [args.init_position],
    'feed_delay': int(args.feed_delay),
    'feed_duration': int(args.feed_duration),
    'iti_min': 240  # with some variance
}
lincoln(log=f"{args.birdID}_{__name__}.log", level=args.log_level)
logger = logging.getLogger('main')


async def main():
    # Start logging
    global decider
    decider = Morgoth()
    await contact_host()
    asyncio.create_task(decider.messenger.eye())

    await decider.set_light()
    await decider.set_feeder(duration=params['feed_duration'])
    asyncio.create_task(decider.light_cycle())
    if args.fforward or (args.block == 4):
        state['block'] = 4
    else:
        state['block'] = int(args.block)

    logger.info(f"{__name__} initiated")
    await slack(f"{__name__} initiated on {IDENTITY}", usr=args.user)

    while True:
        if not decider.sun.daytime:
            logger.info("Paused")
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

    await decider.feed(delay=params['feed_delay'])
    state.update({
        'trial': state.get('trial', 0) + 1,
    })
    logger.info(f"Trial {state['trial']} completed. iti will be {iti}")
    await post_host(msg=state.copy(), target='trials')

    await asyncio.sleep(iti)
    if state['trial'] + 1 > params['block_length']:
        state.update({
            'trial': 0,
            'block': state.get('block', 0) + 1,
        })


async def block1_patience():
    await decider.cues_off()
    iti_var = 60
    await_input = peck_parse(params['init_position'], 'r')
    cue_pos = peck_parse(params['init_position'], 'l')

    iti = int(params['iti_min'] + random.random() * iti_var)

    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await decider.cue(cue_pos, params['cue_color'])

    def resp_check(key_state):
        for k, v in key_state.items():
            if v & (k == await_input):
                return True
        return False

    responded, msg, rtime = await decider.scry('peck-keys',
                                               condition=resp_check,
                                               timeout=params['response_duration'])

    # feed regardless of response
    await decider.cue(cue_pos, 'off')
    await decider.feed(delay=params['feed_delay'])

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

    logger.info(f"Trial {state['trial']} completed. iti will be {iti}")
    await post_host(msg=state.copy(), target='trials')
    await asyncio.sleep(iti)

    if responded or (state['trial'] + 1 > params['block_length']):
        state.update({
            'trial': 0,
            'block': state.get('block', 0) + 1,
        })


async def block2_peck():
    await decider.cues_off()
    iti_var = 15
    iti = int(random.random() * iti_var)
    await_input = peck_parse(params['init_position'], 'r')
    cue_pos = peck_parse(params['init_position'], 'l')

    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await decider.cue(cue_pos, params['cue_color'])

    def resp_check(key_state):
        for k, v in key_state.items():
            if v & (k == await_input):
                return True
        return False

    responded, msg, rtime = await decider.scry('peck-keys',
                                               condition=resp_check,
                                               timeout=None)

    # feed regardless of response
    await decider.cue(await_input, 'off')
    if responded:  # should always be True in this block
        await decider.feed(delay=params['feed_delay'])
        state.update({
            'trial': state.get('trial', 0) + 1,
            'result': 'feed',
            'response': await_input,
            'rtime': rtime,
        })
        logger.info(f"Trial {state['trial']} completed. iti will be {iti}")
        await post_host(msg=state.copy(), target='trials')
        await asyncio.sleep(iti)

        if state['trial'] + 1 > params['block_length']:
            state.update({
                'trial': 0,
                'block': state.get('block', 0) + 1,
            })
    else:
        raise Exception("Block 2 passed without any response!")


async def block3_extend():
    await decider.cues_off()
    iti_var = 15
    iti = int(random.random() * iti_var)
    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await_input = peck_parse(params['init_position'], 'r')
    await decider.cue(params['init_position'], params['cue_color'])

    def resp_check(key_state):
        for k, v in key_state.items():
            if v & (k == await_input):
                return True
        return False

    await decider.scry('peck-keys',
                       condition=resp_check,
                       timeout=None)
    await decider.cue(params['init_position'], 'off')

    cue2 = pick(params['response_position'])
    second_input = peck_parse(cue2, 'r')
    await decider.cue(cue2, params['cue_color'])

    def resp_check(key_state):
        for k, v in key_state.items():
            if v & (k == second_input):
                return True
            return False

    responded, msg, rtime = await decider.scry('peck-keys',
                                               condition=resp_check,
                                               timeout=None)
    await decider.cue(cue2, 'off')

    await decider.feed(delay=params['feed_delay'])

    state.update({
        'trial': state.get('trial', 0) + 1,
        'result': 'feed',
        'response': second_input,
        'rtime': rtime,
    })
    logger.info(f"Trial {state['trial']} completed. iti will be {iti}")
    await post_host(msg=state.copy(), target='trials')
    await asyncio.sleep(iti)

    if state['trial'] + 1 > params['block_length']:
        state.update({
            'trial': 0,
            'block': state.get('block', 0) + 1,
        })


async def block4_auton():
    await decider.cues_off()
    iti_var = 15
    iti = int(random.random() * iti_var)
    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await_input = peck_parse(params['init_position'], 'r')

    def resp_check(key_state):
        for k, v in key_state.items():
            if v & (k == await_input):
                return True
        return False

    await decider.scry('peck-keys',
                       condition=resp_check,
                       timeout=None)

    cue2 = pick(params['response_position'])
    second_input = peck_parse(cue2, 'r')
    await decider.cue(cue2, params['cue_color'])

    def resp_check(key_state):
        for k, v in key_state.items():
            if v & (k == second_input):
                return True
        return False

    responded, msg, rtime = await decider.scry('peck-keys',
                                               condition=resp_check,
                                               timeout=None)
    await decider.cue(cue2, 'off')

    await decider.feed(delay=params['feed_delay'])

    state.update({
        'trial': state.get('trial', 0) + 1,
        'result': 'feed',
        'response': second_input,
        'rtime': rtime,
    })
    logger.info(f"Trial {state['trial']} completed. iti will be {iti}")
    await post_host(msg=state.copy(), target='trials')
    await asyncio.sleep(iti)

    if state['trial'] == params['block_length']:
        await slack(f"Interrupt Shape completed for {state['subject']}. Trials will continue running",
                    usr=params['user'])
        logger.info('Shape completed')


def pick(group):
    return group[int(random.random() // (1 / len(group)))]


if __name__ == 'shape':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt Detected, shutting down.")
        sys.exit("Keyboard Interrupt Detected, shutting down.")
    except Exception as e:
        logger.error(f"Error encountered {e}")
        asyncio.run(slack(f"{__name__} client encountered and error and has shut down.", usr=args.user))
        print(e)
        sys.exit("Error Detected, shutting down.")
