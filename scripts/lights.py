#!/usr/bin/python3
import sys
import argparse
import asyncio
import logging
import random
from lib.logging import lincoln
from lib.process import *
from lib.dispatch import *


__name__ = 'lights'

p = argparse.ArgumentParser()
p.add_argument("birdID")
p.add_argument("user")
p.add_argument("--feed", help="run food motor at defined interval",
               action='store_true')
p.add_argument("--feed_interval", help="interval between feeding (in ms)",
               action='store', type=int, default=30000)
p.add_argument("--feed_duration", help="default feeding duration (in ms)",
               action='store', type=int, default=4000)
p.add_argument('--log_level', default='INFO')
args = p.parse_args()

lincoln(log=f"{args.birdID}_{__name__}.log", level=args.log_level)
logger = logging.getLogger('main')


async def feed():
    try:
        logger.info(f"Feeding requested at intervals of {args.feed_duration} ms. Setting parameters.")
        await decider.set_feeder(duration=int(args.feed_duration))
        while True:
            logger.info("Feeding.")
            await decider.feed()
            await asyncio.sleep(int(args.feed_interval) / 1000)  # sleep in seconds
    except asyncio.CancelledError:
        logger.warning("Feed loop has been cancelled due to another task's failure.")


async def main():
    global decider
    decider = Morgoth()
    await contact_host()
    # House-lights
    await decider.set_light()

    logging.info("Lights.py initiated")
    slack(f"lights.py initiated on {IDENTITY}", usr=args.user)

    try:
        if args.feed:
            await asyncio.gather(
                decider.messenger.eye(), decider.light_cycle(), feed(),
                return_exceptions=False
            )
        else:
            await asyncio.gather(
                decider.messenger.eye(), decider.light_cycle(),
                return_exceptions=False
            )
    except Exception as error:
        import traceback
        logger.error(f"Error encountered: {error}")
        print(traceback.format_exc())
        slack(f"{__name__} client encountered and error and will shut down.", usr=args.user)
        sys.exit("Error Detected, shutting down.")


if __name__ == "lights":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt Detected, shutting down.")
        slack(f"{__name__} client was manually shut down.", usr=args.user)
        sys.exit("Keyboard Interrupt Detected, shutting down.")


