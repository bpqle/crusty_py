from connect import Request, decide_poll
from components import Components
import asyncio
import time
import logging
import zmq
import zmq.asyncio
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop
logger = logging.getLogger(__name__)
loop = IOLoop.current()


async def log_trial():
    return


async def lights_up():
    return


async def feeder():
    return


async def slack():
    return


async def make_stream(component: str, callback):
    ctx = zmq.asyncio.Context()
    subsock = ctx.socket(zmq.SUB)
    logger.debug("Created decide-core subscriber")
    stream = ZMQStream(subsock)
    return stream
