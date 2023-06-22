import sys
import os
import asyncio
import time
import logging

cpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))
sys.path.insert(1, libpath)
sys.path.insert(1, cpath)
from lib.connect import Request, decide_poll
from lib.components import Component


components = ['house-light', 'stepper-motor',
              'peck-leds-left', 'peck-leds-center', 'peck-leds-right',
              'peck-keys', 'audio-playback']


async def paramelize():
    req_body = {
        'clock_interval': 300
    }
    req = Request('SetParameters', 'house-light', req_body)
    rep = await req.send()
    logging.info(f"Reply from decide-rs: {rep}")

    req_body = {
        'timeout': 2000
    }
    req = Request('SetParameters', 'stepper-motor', req_body)
    rep = await req.send()
    logging.info(f"Reply from decide-rs: {rep}")


async def lights_up(brightness):
    logging.info(f"Changing lights to {brightness}")
    hl_state = {
        'manual': True,
        'brightness': brightness,
    }
    req = Request(request_type="ChangeState",
                  component='house-light',
                  body=hl_state)
    rep = await req.send()
    logging.info(f"Reply from decide-rs: {rep}")


async def main():

    logging.basicConfig(stream=sys.stdout, format='%(asctime)s : %(message)s', level=logging.DEBUG)
    logging.info("Lights initiating, connecting to decide-core.")
    poller = asyncio.create_task(decide_poll(components))
    await asyncio.create_task(paramelize())
    await asyncio.sleep(3)
    await lights_up(20)
    await asyncio.sleep(3)
    await lights_up(50)
    await asyncio.sleep(5)
    await poller


if __name__ == "__main__":
    asyncio.run(main())
