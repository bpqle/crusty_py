#!/usr/bin/python3

import sys
sys.path.insert(1, libpath)
sys.path.insert(1, cpath)
from lib.device import *
from lib.control import *
import os
import asyncio
import logging
import argparse
import zmq

cpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))

__exp__ = 'lights'

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
    light = await Sun.spawn(interval=300)
    logger.info(type(light))
    logger.info(light.interval)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    streamer = logging.StreamHandler(sys.stdout)
    streamer.setFormatter(formatter)
    filer = logging.FileHandler(f"{args.birdID}_{__exp__}.log", mode='w')
    filer.setFormatter(formatter)
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[filer, streamer]
    )

    logging.info("Lights.py initiated")
    lightyear = asyncio.create_task(light.cycle())
    if args.feed:
        logger.info("Feeding requested.")
        try:
            while True:
                logger.info("Feeding.")
                await feed(args.feed_duration, context=context)
                await asyncio.sleep(args.feed_interval/1000)  # sleep in seconds
        except KeyboardInterrupt:
            await slack("PyCrust Lights is shutting down", usr=args.user)
    else:
        await lightyear


if __name__ == "__main__":
    asyncio.run(main())
