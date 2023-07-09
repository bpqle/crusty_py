#!/usr/bin/python3
import os
import sys
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))
sys.path.insert(1, libpath)
from lib.device import *
from lib.control import *
import asyncio
import logging
import argparse
import zmq

__exp__ = 'lights'
HOSTNAME = os.uname()[1]

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


async def main():
    context = zmq.Context()

    await lincoln(log=f"{args.birdID}_{__exp__}.log")

    logging.info("Lights.py initiated")
    light = await Sun.spawn(interval=300)
    lightyear = asyncio.create_task(light.cycle())
    await slack(f"lights.py initiated on {HOSTNAME}", usr=args.user)
    if args.feed:
        logger.info(f"Feeding requested at intervals of {args.feed_duration} ms. Setting parameters.")
        await set_feeder(args.feed_duration)
        try:
            while True:
                logger.info("Feeding.")
                await feed(args.feed_duration)
                await asyncio.sleep(args.feed_interval/1000)  # sleep in seconds
        except KeyboardInterrupt:
            await slack("PyCrust Lights is shutting down", usr=args.user)
    else:
        await lightyear


if __name__ == "__main__":
    asyncio.run(main())
