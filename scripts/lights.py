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


async def main():
    # Start logging
    global decider
    decider = Morgoth()
    await contact_host()
    # House-lights
    await decider.set_light()
    lights = asyncio.create_task(decider.light_cycle())

    logging.info("Lights.py initiated")

    await slack(f"lights.py initiated on {IDENTITY}", usr=args.user)

    if args.feed:
        logger.info(f"Feeding requested at intervals of {args.feed_duration} ms. Setting parameters.")
        await decider.set_feeder(duration=int(args.feed_duration))
        while True:
            logger.info("Feeding.")
            await decider.feed()
            await asyncio.sleep(int(args.feed_interval) / 1000)  # sleep in seconds
    else:
        await lights


if __name__ == "lights":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt Detected, shutting down.")
        sys.exit("Keyboard Interrupt Detected, shutting down.")
    except Exception as e:
        logger.error(f"Error encountered {e}")
        print(e)
        asyncio.run(slack(f"{__name__} client encountered and error and has shut down.", usr=args.user))
        sys.exit("Error Detected, shutting down.")

