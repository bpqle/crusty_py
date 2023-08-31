#!/usr/bin/python3

import os
import sys
import argparse
import asyncio
import logging
import traceback
sys.path.append(os.path.abspath("../scripts"))
from scripts.lib.process import *
from scripts.lib.logging import *
from scripts.lib.dispatch import *

# Test playback functionality, including interruption.
__name__ = 'playback_test'

LOCAL_LOG = False
CONTACT_HOST = False
lincoln(log=f"playback_test.log", level='DEBUG')
logger = logging.getLogger('main')


async def main():
    global decider
    decider = Morgoth()
    asyncio.create_task(decider.messenger.eye())
    await decider.init_playback('interrupt_playback.json', replace=False)

    stim_data = decider.playback.next()
    logger.info('Begin requesting playback.')
    await decider.play(stim_data['name'])
    logger.info('Playback completed. Moving on.')

    await asyncio.sleep(2)

    stim_data = decider.playback.next()
    logger.info("Begin requesting playback. Will interrupt")
    await decider.play(stim_data['name'], poll_end=False)
    duration = decider.playback.duration
    logger.info(f"Stimuli length will be {duration}s")
    await asyncio.sleep(2)
    await decider.stop()
    logger.info("Playback interruption passed.")

    await asyncio.sleep(2)
    stim_data = decider.playback.next()
    logger.info('Begin requesting playback.')
    await decider.play(stim_data['name'])
    logger.info('Playback completed. Moving on.')

    await asyncio.sleep(2)

    stim_data = decider.playback.next()
    logger.info("Begin requesting playback. Will interrupt")
    await decider.play(stim_data['name'], poll_end=False)
    duration = decider.playback.duration
    logger.info(f"Stimuli length will be {duration}s")
    await asyncio.sleep(2)
    await decider.stop()
    logger.info("Playback interruption passed. Test complete.")


if __name__ == "playback_test":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt Detected, pausing test.")
        sys.exit("Keyboard Interrupt Detected, pausing test.")
    except Exception as e:
        logger.error(f"Error encountered {traceback.format_exc()}")
        traceback.print_exc()
        sys.exit("Error Detected, shutting down.")
