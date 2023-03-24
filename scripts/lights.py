import sys
import os
cpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))
sys.path.insert(1, libpath)
sys.path.insert(1, cpath)
import lib.house_light as hl_proto
import lib.peckboard as pb_proto
import lib.sound_alsa as sa_proto
import lib.stepper_motor as sm_proto
from lib.communicate import Request, req_from_mtp, decide_poll

import zmq
import asyncio
import zmq.asyncio
import time
import logging

REQ_ENDPOINT = "tcp://127.0.0.1:7897"
PUB_ENDPOINT = "tcp://127.0.0.1:7898"

exp = {
    'name': 'lights'
}
components = ['house-light', 'stepper-motor',
              'peck-leds-left', 'peck-leds-center', 'peck-leds-right',
              'peck-keys', 'audio-playback']


async def paramelize():
    hl_param = hl_proto.HlParams(clock_interval=300)
    sm_param = sm_proto.SmParams(timeout=4000)
    req1 = Request(request_type='SetParameters',
                   component=b'house-light',
                   body=hl_param.__bytes__())
    reply1 = await req1.send()
    print(reply1)
    req2 = Request(request_type='SetParameters',
                   component=b'stepper-motor',
                   body=bytes(sm_param))
    reply2 = await req2.send()
    print(reply2)


async def main():
    logging.info("lights.py initiated, connecting to decide-core.")
    asyncio.create_task(paramelize())
    asyncio.create_task(decide_poll(components))


if __name__ == "__main__":
    asyncio.run(main())
