import asyncio
import zmq
import zmq.asyncio
from enum import Enum
from lib.generator_hex import decide_pb2 as dc_db
import logging
import time
from .inform import *
from .decrypt import Component
logger = logging.getLogger(__name__)


class RequestType(Enum):
    ChangeState = 0x00
    ResetState = 0x01
    SetParameters = 0x02
    GetParameters = 0x12
    ComponentShutdown = 0x13
    RequestLock = 0x20
    ReleaseLock = 0x21
    Shutdown = 0x22


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

    async def send(self, timeout=TIMEOUT):
        multi_msg = [DECIDE_VERSION, self.type_encode, self.body]
        if self.component is not None:
            multi_msg.append(self.component.encode('utf-8'))

        ctx = zmq.asyncio.Context.instance()
        req_sock = ctx.socket(zmq.REQ)
        req_sock.connect(REQ_ENDPOINT)
        logger.debug(f"{self.request_type} - {self.component} Request Socket Created")
        await req_sock.send_multipart(multi_msg)
        logger.debug(f"{self.request_type} - {self.component}  Request sent, awaiting reply")

        poll_res = await req_sock.poll(timeout)
        if poll_res == zmq.POLLIN:
            *dc, reply = await req_sock.recv_multipart()
            logger.debug(f" {self.request_type} - {self.component}  Reply received '{reply}'")
            if dc[0] != DECIDE_VERSION:
                logger.warning(f"Mismatch Version of DECIDE-RS in reply {dc[0]}")

            # Parse Reply:
            rep_template = dc_db.Reply()
            rep_template.ParseFromString(reply)
            result = rep_template.WhichOneof('result')
            logger.debug(f" {self.request_type} - {self.component}  Reply parsed as {result}")
            if result == 'ok':
                return
            elif result == 'error':
                logger.error(f"Reply error from decide-rs: {rep_template.result}")
            elif result == 'params':  # decode params
                any_params = rep_template.params
                part = Component('param', self.component)
                params = await part.from_any(any_params)
                return params
        else:  # timeout awaiting response
            logger.error(f"{self.request_type} - {self.component}"
                         f" Timed out after {timeout}ms awaiting response from decide-rs")


async def stayin_alive(**kwargs):
    ctx = zmq.asyncio.Context.instance()
    while True:
        try:
            ctx.socket(zmq.PUB).bind(PUB_ENDPOINT)
        except:
            continue
        else:
            logger.error("Client was able to bind to PUB_ENDPOINT, decide-rs may be unresponsive")
            await slack(f"Decide-rs unresponsive on {kwargs['address']}, shutting down client", usr=kwargs['user'])
            raise


# Await state change from component with optional timeout
# If caught returns True or timeout occurs, record time and return with msg if available
# If failure is specified, will call the function upon timeout
async def catch(components, caught, failure=None, timeout=None, **kwargs):
    ctx = zmq.asyncio.Context.instance()
    poller = zmq.asyncio.Poller()
    if isinstance(components, str):
        subber = ctx.socket(zmq.SUB)
        subber.connect(PUB_ENDPOINT)
        subber.subscribe(f"state/{components}".encode('utf-8'))
        poller.register(subber, zmq.POLLIN)
    elif isinstance(components, list):
        for c in components:
            subber = ctx.socket(zmq.SUB)
            subber.connect(PUB_ENDPOINT)
            subber.subscribe(f"state/{c}".encode('utf-8'))
            poller.register(subber, zmq.POLLIN)

    interrupted = False
    message = None
    timer = None

    async def test(polt, func):
        nonlocal interrupted, message, start, timer
        while True:
            poll_res = await polt.poll()
            assert isinstance(poll_res, list)
            for (sock, flag) in poll_res:
                if flag == zmq.POLLIN:
                    *topic, msg = await sock.recv_multipart(zmq.DONTWAIT)
                    state, comp = topic[0].decode("utf-8").split("/")
                    component = Component(state, comp)
                    tstamp, state_msg = await component.from_pub(msg)
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
            await asyncio.wait_for(test(poller, caught), timeout)
        except TimeoutError:
            message = None
            timer = timeout
            if failure is not None:
                failure(interrupted)
    else:
        await test(poller, caught)

    return interrupted, message, timer

