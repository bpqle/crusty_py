import asyncio
import time
import random
import zmq
import zmq.asyncio
import yaml
import logging

logger = logging.getLogger(__name__)

class Zim:
    @classmethod
    async def spawn(cls):
        self = Zim()

        with open("/root/.config/decide-rs/config.yml", "r") as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError:
                logger.error("Unable to load decide-rs config")

        self.components = config.keys()
        ctx = zmq.asyncio.Context.instance()
        poller = zmq.asyncio.Poller()
        for c in self.components:
            subber = ctx.socket(zmq.SUB)
            subber.connect(PUB_ENDPOINT)
            subber.subscribe(f"state/{c}".encode('utf-8'))
            poller.register(subber, zmq.POLLIN)

    async def ger_fetch(self, component):