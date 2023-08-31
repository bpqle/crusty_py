#!/usr/bin/python3
import sys
import argparse
import asyncio
import logging
import random
from lib.logging import lincoln
from lib.process import *
from lib.dispatch import *


__name__ = 'gng'

p = argparse.ArgumentParser()
p.add_argument("birdID")
p.add_argument("user")
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
p.add_argument('--log_level', default='INFO')
args = p.parse_args()

state = {
    'subject': args.birdID,  # logged
    'experiment': args.config,  # logged
    'name': __name__,  # logged
    'trial': 0,  # logged
    'result': None,  # logged
    'correct': False,  # logged
    'response': None,  # logged
    'rtime': None,  # logged
    'correction': 0,  # logged
    'stimulus': None,  # logged
}
params = {
    'user': args.user,
    'active': True,
    'response_duration': int(args.response_duration)/1000,
    'feed_duration': int(args.feed_duration),
    'punish_duration': int(args.lightsout_duration),
    'max_corrections': int(args.max_corrections),
    'replace': args.replace,
    'correction_timeout': args.correction_timeout,
    'cue_frequency': args.cue_frequency,
    'cue_color': args.cue_color,
    'feed_delay': int(args.feed_delay),
    'min_iti': 100,
    'init_key': args.init_position,
}

lincoln(log=f"{args.birdID}_{__name__}.log", level=args.log_level)
logger = logging.getLogger('main')


async def await_init():
    logger.state("Awaiting init")
    await_input = peck_parse(params['init_key'], 'r')

    def peck_init(key_msg):
        if (await_input in key_msg) and (key_msg[await_input]):
            return True
    await decider.scry(
        'peck-keys',
        condition=peck_init,
    )


async def present_stim(stim_data):
    logger.state('Peck init registered, presenting stim')
    await decider.play(stim_data['name'])
    return


async def await_response(stim_data, correction):
    logger.state("Awaiting response")
    if (correction > 0) and correction_check(correction):
        cue_loc = peck_parse(decider.playback.current_cue(), 'l')
        await decider.cue(cue_loc, params['cue_color'])
    else:
        cue_loc = None
    response = 'timeout'
    logger.debug(stim_data)

    def resp_check(pub_msg):
        nonlocal response
        for k, v in pub_msg.items():
            if (k in stim_data['responses']) & bool(v):
                response = k
                return True
        return False

    responded, _, rtime = await decider.scry(
        'peck-keys',
        condition=resp_check,
        timeout=params['response_duration']
    )

    if not responded:
        return response, None, cue_loc
    else:
        return response, rtime, cue_loc


async def complete(cue_loc, stim_data, correction, response, rtime):
    logger.state("At trial exit")
    if cue_loc:
        await decider.cue(cue_loc, 'off')
    # Determine outcome
    outcome = stim_data['responses'][response]
    rand = random.random()
    if outcome['correct']:
        if outcome['p_reward'] >= rand:
            await decider.feed(params['feed_delay']/1000)
        result = 'feed'
    else:
        if outcome['p_punish'] >= rand:
            await decider.blip(params['punish_duration'])
        result = 'no_feed'
    # Log Trial
    state.update({
        'trial': state.get('trial', 0) + 1,
        'result': result,
        'response': response,
        'rtime': rtime,
        'correct': outcome['correct'],
        'correction': correction,
        'stimulus': stim_data['name']
    })
    logger.info(f"Trial {state['trial']} completed. Logging trial.")
    await post_host(msg=state.copy(), target='trials')
    # Advance
    if (response == 'timeout') & params['correction_timeout']:
        correction += 1
        logger.debug("Response was timeout, next trial is correction trial.")
    elif (response != 'timeout') & (not outcome['correct']) & (correction < params['max_corrections']):
        correction += 1
        logger.debug("Next Trial correction.")
    else:
        correction = 0
        stim_data = decider.playback.next()
    return stim_data, correction


def correction_check(correction):
    if params['cue_frequency'] == 'never':
        return False
    elif params['cue_frequency'] == 'always':
        return True
    elif params['cue_frequency'] == 'sometimes':
        return np.exp(correction / params['max_corrections']) >= random.random()


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

    correction = 0
    stim_data = decider.playback.next()

    logger.info(f"{__name__} initiated")
    await slack(f"{__name__} initiated on {IDENTITY}", usr=args.user)

    while True:
        await await_init()
        await present_stim(stim_data)
        response, rtime, cue_loc = await await_response(stim_data, correction)
        stim_data, correction = await complete(cue_loc, stim_data, correction, response, rtime)


if __name__ == "gng":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt Detected, shutting down.")
        sys.exit("Keyboard Interrupt Detected, shutting down.")
    except Exception as e:
        import traceback
        logger.error(f"Error encountered: {e}")
        print(traceback.format_exc())
        asyncio.run(slack(f"{__name__} client encountered and error and will shut down.", usr=args.user))
        sys.exit("Error Detected, shutting down.")

