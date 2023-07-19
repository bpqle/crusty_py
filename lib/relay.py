import asyncio
import time
import random
import zmq
import zmq.asyncio
import logging
from enum import Enum
from .inform import *
from .decrypt import Component
from lib.generator_hex import decide_pb2 as dc_db
from google.protobuf.json_format import MessageToDict
logger = logging.getLogger(__name__)

class Sauron:
    def __init__(self):
        context = zmq.asyncio.Context()

        self.subber = context.socket(zmq.SUB)
        self.subber.connect(PUB_ENDPOINT)

        self.caller = context.socket(zmq.REQ)
        self.caller.connect(REQ_ENDPOINT)

    async def request(self, request_type: str, component: str, body=None):
        req = await Request.spawn(request_type, component, body)
        message = [DECIDE_VERSION, req.type_encode, req.body]
        if component is not None:
            message.append(component.encode('utf-8'))
        await self.caller.send_multipart(message)

        poll_res = await self.caller.poll(TIMEOUT)
        if poll_res == zmq.POLLIN:
            *dc, reply = await self.caller.recv_multipart()
            logger.debug(f" {request_type} - {component}  Reply received '{reply}'")
            if dc[0] != DECIDE_VERSION:
                logger.warning(f"Mismatch Version of DECIDE-RS in reply {dc[0]}")

            # Parse Reply:
            rep_template = dc_db.Reply()
            rep_template.ParseFromString(reply)
            result = rep_template.WhichOneof('result')
            logger.debug(f" {request_type} - {component}  Reply parsed as {result}")
            if result == 'ok':
                return
            elif result == 'error':
                logger.error(f"Reply error from decide-rs: {rep_template.result}")
            elif result == 'params':  # decode params
                any_params = rep_template.params
                part = Component('param', component)
                params = await part.from_any(any_params)
                return params
        else:  # timeout awaiting response
            logger.error(f"{request_type} - {component}"
                         f" Timed out after {TIMEOUT}ms awaiting response from decide-rs")

    async def scry(self, component, condition, failure=None, timeout=None):
        logger.info(f"Process started for {component}")
        if isinstance(component, str):
            self.subber.subscribe(f"state/{component}".encode('utf-8'))
        # elif isinstance(component, list):
        #     for c in component:
        #         self.subber.subscribe(f"state/{c}".encode('utf-8'))

        interrupted = False
        message = None
        timer = None

        async def test(sock, func):
            nonlocal interrupted, message, start, timer
            while True:
                *topic, msg = await sock.recv_multipart(zmq.DONTWAIT)
                state, comp = topic[0].decode("utf-8").split("/")
                proto_comp = Component(state, comp)
                tstamp, state_msg = await proto_comp.from_pub(msg)
                if func(state_msg):
                    end = time.time()
                    timer = end - start
                    message = state_msg
                    interrupted = True
                    return
                else:
                    continue

        start = time.time()
        if timeout is not None:
            try:
                await asyncio.wait_for(test(self.subber, condition), timeout)
            except TimeoutError:
                message = None
                timer = timeout
                if failure is not None:
                    failure(component)
        else:
            await test(self.subber, condition)

        self.subber.unsubscribe(f"state/{component}")
        return interrupted, message, timer


class Request:
    @classmethod
    async def spawn(cls, request_type: str, component: str, body=None):
        self = Request()
        logger.debug(f"{request_type} - {component} Initiating Request.")
        if request_type in ["SetParameters", "GetParameters"]:
            body_encode = Component('param', component, data=body)
            request = await body_encode.to_req()
        elif request_type in ["ChangeState", "GetState"]:
            body_encode = Component('state', component, data=body)
            request = await body_encode.to_req()
        else:
            logger.error(f"Unsupported Request Type {request_type} for {component}")
            raise
        self.request_type = request_type
        self.type_encode = RequestType[request_type].value.to_bytes(2, 'little')
        self.component = component
        self.body = request.SerializeToString()
        logger.debug(f"{request_type} - {component} Req Serialized to String")
        return self


class RequestType(Enum):
    ChangeState = 0x00
    ResetState = 0x01
    SetParameters = 0x02
    GetParameters = 0x12
    ComponentShutdown = 0x13
    RequestLock = 0x20
    ReleaseLock = 0x21
    Shutdown = 0x22

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