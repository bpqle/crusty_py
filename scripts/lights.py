#!/usr/bin/python3
import os
import sys
sys.path.append(os.path.abspath(".."))
from lib.process import *
from lib.inform import *
import asyncio
import logging
import argparse
import zmq

__name__ = 'lights'

p = argparse.ArgumentParser()
p.add_argument("user")
p.add_argument("birdID")
p.add_argument("--feed", help="run food motor at defined interval",
               action='store_true')
p.add_argument("--feed_interval", help="interval between feeding (in ms)",
               action='store', type=int, default=30000)
p.add_argument("--feed_duration", help="default feeding duration (in ms)",
               action='store', type=int, default=4000)
args = p.parse_args()
lincoln(log=f"{args.birdID}_{__name__}.log")
decider = Morgoth()


async def main():
    # Start logging
    await contact_host()

    lights = asyncio.create_task(decider.keep_alight())

    await slack(f"lights.py initiated on {IDENTITY}", usr=args.user)

    if args.feed:
        logger.info(f"Feeding requested at intervals of {args.feed_duration} ms. Setting parameters.")
        await decider.set_feeder(duration=args.feed_duration)
        while True:
            logger.info("Feeding.")
            await decider.feed()
            await asyncio.sleep(args.feed_interval / 1000)  # sleep in seconds
    else:
        await lights


if __name__ == "lights":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.error("SIGNINT detected. Shutting down")
        asyncio.run(slack("PyCrust Lights is shutting down", usr=args.user))

