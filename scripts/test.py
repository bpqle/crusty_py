import sys
import os
cpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))
sys.path.insert(1, libpath)
sys.path.insert(1, cpath)

from lib.connect import Request, decide_poll
import asyncio
import time
import logging


components = ['house-light', 'stepper-motor',
              'peck-leds-left', 'peck-leds-center', 'peck-leds-right',
              'peck-keys', 'audio-playback']


async def main():

    logging.basicConfig(stream=sys.stdout, format='%(asctime)s : %(message)s', level=logging.DEBUG)
    logging.info("Lights initiating, connecting to decide-core.")
    poller = asyncio.create_task(decide_poll(components))
    await asyncio.create_task(paramelize())
    await asyncio.sleep(3)
    await lights_up(20)
    await asyncio.sleep(3)
    await lights_auto()
    await asyncio.sleep(3)
    await led_check()
    await asyncio.sleep(3)
    await motor()
    await asyncio.sleep(3)
    await req_song('dhhon79k_30.wav')
    await asyncio.sleep(3)
    await poller


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

    req_body = {
        'audio_dir': '/root/clean_stim'
    }
    req = Request('SetParameters', 'sound-alsa', req_body)
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


async def lights_auto():
    logging.info(f"Changing lights to ephemera mode")
    hl_state = {
        'manual': False,
        'ephemera': True,
    }
    req = Request(request_type="ChangeState",
                  component='house-light',
                  body=hl_state)
    rep = await req.send()
    logging.info(f"Reply from decide-rs: {rep}")


async def req_song(song):
    logging.info(f"requesting stimuli {song}")
    sa_state = {
        'audio_id': song,
        'playback': 1,
    }
    req = Request(request_type="ChangeState",
                  component='sound-alsa',
                  body=sa_state)
    rep = await req.send()
    logging.info(f"Reply from decide-rs: {rep}")


async def led_check():
    led_state = {
        'led_state': 'blue',
    }
    for l in ['left', 'right', 'center']:
        req = Request(request_type="ChangeState",
                      component='peck-leds-'+l,
                      body=led_state)
        rep = await req.send()
        logging.info(f"Reply from decide-rs: {rep}")


async def motor():
    logging.info(f"Running motor")
    sm_state = {
        'running': True,
        'direction': True,
    }
    req = Request(request_type="ChangeState",
                  component='stepper-motor',
                  body=sm_state)
    rep = await req.send()
    logging.info(f"Reply from decide-rs: {rep}")


if __name__ == "__main__":
    asyncio.run(main())
