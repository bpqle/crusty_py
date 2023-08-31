#!/usr/bin/python3
import sys
import argparse
import asyncio
import logging
import random
from lib.logging import lincoln
from lib.process import *
from lib.dispatch import *


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
    'min_iti': 100,
    'init_key': args.init_position,
}
lincoln(log=f"{args.birdID}_{__name__}.log", level=args.log_level)
logger = logging.getLogger('main')


async def await_init():
    logger.state("Awaiting Init")
    await_input = peck_parse(params['init_key'], 'r')

    def peck_init(key_state):
        if (await_input in key_state) and (key_state[await_input]):
            return True
    await decider.scry(
        'peck-keys',
        condition=peck_init,
    )


async def present_stim(stim_data):
    logger.state("Presenting stimuli")
    await decider.play(stim_data['name'], poll_end=False)
    return


async def await_response(stim_data):
    logger.state("Awaiting response")
    response = 'timeout'
    duration = decider.playback.duration

    def resp_check(key_state):
        nonlocal response
        for k, v in key_state.items():
            if (k in stim_data['responses']) & bool(v):
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
    logger.state("At trial exit")
    # Determine outcome
    outcome = stim_data['responses'][response]
    rand = random.random()
    result = 'no_feed'
    if outcome['reinforced']:
        if outcome['p_reward'] >= rand:
            await decider.feed(params['feed_delay']/1000)
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
    # Initiate apparatus
    global decider
    decider = Morgoth()
    # Start logging for messages
    await contact_host()
    asyncio.create_task(decider.messenger.eye())
    # Initialize components
    await decider.set_light()
    await decider.set_feeder(duration=params['feed_duration'])
    await decider.init_playback(args.config, replace=args.replace)
    asyncio.create_task(decider.light_cycle())
    # Get first stimulus
    stim_data = decider.playback.next()

    logger.info(f"{__name__} initiated")
    await slack(f"{__name__} initiated on {IDENTITY}", usr=args.user)

    response = None
    while True:
        if (response is None) or (response == 'timeout'):
            await await_init()
        duration = await present_stim(stim_data)
        response, rtime = await await_response(stim_data)
        stim_data = await complete(stim_data, response, rtime)


if __name__ == "interrupt-gng":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt Detected, shutting down.")
        sys.exit("Keyboard Interrupt Detected, shutting down.")
    except Exception as e:
        logger.error(f"Error encountered {e}")
        print(e)
        asyncio.run(slack(f"{__name__} client encountered and error and will shut down.", usr=args.user))
        sys.exit("Error Detected, shutting down.")

