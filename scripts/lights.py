#!/usr/bin/python3
import os
import sys
sys.path.append(os.path.abspath(".."))
from lib.engine import *
from lib.inform import *
import asyncio
import logging
import argparse
import zmq

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
    # Check status of decide-rs
    bg = asyncio.create_task(stayin_alive(address=HOSTNAME, user=args.user))
    # Start logging
    await lincoln(log=f"{args.birdID}_{__exp__}.log")
    # House-lights
    logging.info("Lights.py initiated")
    light = await Sun.spawn(interval=300)
    lightyear = asyncio.create_task(light.cycle())

    await slack(f"lights.py initiated on {HOSTNAME}", usr=args.user)

    if args.feed:
        logger.info(f"Feeding requested at intervals of {args.feed_duration} ms. Setting parameters.")
        await set_feeder(args.feed_duration)
        while True:
            logger.info("Feeding.")
            await feed(args.feed_duration)
            await asyncio.sleep(args.feed_interval / 1000)  # sleep in seconds
    else:
        asyncio.gather(lightyear, bg)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.error("SIGNINT detected. Shutting down")
        asyncio.run(slack("PyCrust Lights is shutting down", usr=args.user))

