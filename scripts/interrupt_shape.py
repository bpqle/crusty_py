#!/usr/bin/python3
import sys
import argparse
import asyncio
import logging
import random
from lib.logging import lincoln
from lib.process import *
from lib.dispatch import *


__name__ = 'interrupt-shape'

p = argparse.ArgumentParser()
p.add_argument("birdID")
p.add_argument("user")
p.add_argument("-B", "--block", help="skip to specific block", action='store', default=0)
p.add_argument("--color", help="set color of cues",
               choices=['blue', 'red', 'green'], default='blue')
p.add_argument('--init_position', help='key position to initiate trial',
               choices=['left', 'center', 'right'], default='center')
p.add_argument("-T", "--trials", help="length of blocks 2-3", action='store', default=100)
p.add_argument('--feed_delay', help='time (in ms) to wait between response and feeding',
               action='store', default=200)
p.add_argument("--feed_duration", help="default feeding duration for correct responses (in ms)",
               action='store', default=4000)
p.add_argument("--response_duration", help="response window duration (in ms) in block 1",
               action='store', default=6000)
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
    'feed_delay': int(args.feed_delay)/1000,
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

    await decider.set_light()
    await decider.set_feeder(duration=params['feed_duration'])

    logger.info(f"{__name__} initiated")
    slack(f"{__name__} initiated on {IDENTITY}", usr=args.user)

    try:
        await asyncio.gather(
            decider.messenger.eye(), decider.light_cycle(), experiment_loop(),
            return_exceptions=False
        )
    except Exception as error:
        import traceback
        logger.error(f"Error encountered: {error}")
        print(traceback.format_exc())
        slack(f"{__name__} client encountered and error and will shut down.", usr=args.user)
        sys.exit("Error Detected, shutting down.")


async def experiment_loop():
    state['block'] = int(args.block)
    try:
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
                await block3_auton()
            else:
                raise RuntimeError(f"Bad shape block encountered {state['block']}")
    except asyncio.CancelledError:
        logger.warning("Main experiment loop has been cancelled due to another task's failure.")


async def block0_feeder():
    iti_var = 60
    iti = int(params['iti_min'] + random.random() * iti_var)

    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")

    await decider.feed(delay=params['feed_delay'])
    state.update({
        'trial': state.get('trial', 0) + 1,
    })
    logger.info(f"Trial {state['trial']} completed. Logging trial. iti will be {iti}")
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

    iti = int(random.random() * iti_var)

    if state['trial'] == 0:
        await decider.set_feeder(1000)
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
        await decider.set_feeder(params['feed_duration'])

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
        raise RuntimeError("Block 2 passed without any response!")


async def block3_auton():
    iti_var = 15
    iti = int(random.random() * iti_var)

    await_input = peck_parse(params['init_position'], 'r')

    if state['trial'] == 0:
        logger.info(f"Entering block {state['block']}")
        await decider.cues_off()

    def resp_check(key_state):
        for k, v in key_state.items():
            if v & (k == await_input):
                return True
        return False

    responded, msg, rtime = await decider.scry('peck-keys',
                                               condition=resp_check,
                                               timeout=None)

    # feed regardless of response
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

        if state['trial'] == params['block_length']:
            slack(f"Interrupt Shape completed for {state['subject']}. Trials will continue running",
                        usr=params['user'])
            logger.info('Shape completed')
    else:
        raise Exception("Block 3 passed without any response!")


if __name__ == 'interrupt-shape':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt Detected, shutting down.")
        slack(f"{__name__} client was manually shut down.", usr=args.user)
        sys.exit("Keyboard Interrupt Detected, shutting down.")

