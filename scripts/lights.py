import sys
import os
import asyncio
import logging
import argparse
cpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))
sys.path.insert(1, libpath)
sys.path.insert(1, cpath)
from lib.control import *

p = argparse.ArgumentParser()
p.add_argument("user")
p.add_argument("birdID")
p.add_argument("--feed-interval", help="response window duration (in ms)",
               action='store_const', default=30000)
p.add_argument("--feed-duration", help="default feeding duration for correct responses (in ms)",
               action='store_const', default=4000)
args = p.parse_args()

lights = Sun(interval=300)

if __name__ == "__main__":
    asyncio.run(lights.cycle())
    while True:
        feed(args['feed-duration'])
        await asyncio.sleep(args['feed-interval'])
