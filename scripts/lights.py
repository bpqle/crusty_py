import sys
import os
cpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))
sys.path.insert(1, libpath)
sys.path.insert(1, cpath)

from lib.communicate import Request, req_from_mtp, decide_poll

import zmq
import asyncio
import zmq.asyncio
import time
import logging

REQ_ENDPOINT = "tcp://127.0.0.1:7897"
PUB_ENDPOINT = "tcp://127.0.0.1:7898"

components = ['house-light', 'stepper-motor',
              'peck-leds-left', 'peck-leds-center', 'peck-leds-right',
              'peck-keys', 'audio-playback']


async def paramelize():
    req_body = {
        'clock_interval': 300
    }
    req = Request('SetParameters', b'house-light', req_body)
    rep = await req.send()
    print(rep)

    req_body = {
        'timeout': 2000
    }
    req = Request('SetParameters', b'stepper-motor', req_body)
    rep = await req.send()
    print(rep)


async def lightsup(brightness):
    print("Changing lights to ", brightness)
    hl_state = {
        'manual': True,
        'ephemera':  False,
        'brightness': brightness,
        'daytime': True,
    }
    req = Request(request_type="ChangeState",
                  component=b'house-light',
                  body=hl_state)
    rep = await req.send()
    print(rep)


async def main():
    logging.info("lights.py initiated, connecting to decide-core.")
    asyncio.create_task(paramelize())
    poller = asyncio.create_task(decide_poll(components))
    await lightsup(20)
    await asyncio.sleep(4)
    await lightsup(20)
    await asyncio.sleep(4)
    await poller


if __name__ == "__main__":
    asyncio.run(main())
