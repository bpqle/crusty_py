import asyncio
import time
import random
import zmq
import zmq.asyncio
import yaml
import logging
from .decrypt import Component
from .request import Request
from google.protobuf.json_format import MessageToDict
logger = logging.getLogger(__name__)

class Zim:
    @classmethod
    async def spawn(cls, sun_interval=300):
        self = Zim()

        with open("/root/.config/decide-rs/config.yml", "r") as f:
            try:
                rs_conf = yaml.safe_load(f)
            except yaml.YAMLError:
                logger.error("Unable to load decide-rs config")

        self.transient_comps = rs_conf.keys()
        ctx = zmq.asyncio.Context.instance()

        self.sun = await Sun.spawn(interval=sun_interval)

        persistent = zmq.asyncio.Poller()
        self.persistent_comp = ['house-light','peck-keys']
        for c in self.persistent_comp:
            if c in self.transient_comps:
                self.transient_comps.remove(c)
                sub = ctx.socket(zmq.SUB)
                sub.connect(PUB_ENDPOINT)
                sub.subscribe(f"state/{c}".encode('utf-8'))
                persistent.register(sub, zmq.POLLIN)

        self.transient = zmq.asyncio.Poller()
        for c in self.transient_comps:
            sub = ctx.socket(zmq.SUB)
            sub.connect(PUB_ENDPOINT)
            sub.subscribe(f"state/{c}".encode('utf-8'))
            self.transient.register(sub, zmq.POLLIN)

        logger.info("General PUB/SUB setup complete.")

        while True:
            poll_result = await persistent.poll(timeout=1000)
            for (sock, flag) in poll_result:
                if flag == zmq.POLLIN:
                    await self.process_persistent(sock)

    async def process_persistent(self, sock):
        *topic, msg = await sock.recv_multipart(zmq.DONTWAIT)
        state, comp = topic[0].decode("utf-8").split("/")
        component = Component(state, comp)
        tstamp, state_msg = await component.from_pub(msg)
        decoded = MessageToDict(state_msg,
                                preserving_proto_field_name=True)
        if comp == 'house-light':
            self.sun.update(decoded)
        elif comp == 'peck-key':


class Sun:
    def __init__(self):
        self.manual = False
        self.dyson = True
        self.brightness = 0
        self.daytime = True

    @classmethod
    async def spawn(cls, interval):
        self = Sun()
        self.brightness = 0
        self.daytime = False
        self.interval = interval

        param_set = await Request.spawn(request_type="SetParameters",
                                        component='house-light',
                                        body={'clock_interval': self.interval}
                                        )
        await param_set.send()

        interval_check = await Request.spawn(request_type="GetParameters",
                                             component='house-light',
                                             body=None)
        check_res = await interval_check.send()
        if check_res.clock_interval != self.interval:
            logger.error(f"House-Light Clock Interval not set to {self.interval},"
                         f" got {check_res.clock_interval}")

        logger.debug("Sun cycle initiated")
        return self

    def update(self, decoded):
        logger.debug("Updating House-Light from PUB")
        for key, val in decoded.items():
            setattr(self,key,val)