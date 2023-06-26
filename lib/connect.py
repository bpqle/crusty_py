import asyncio
import zmq
import zmq.asyncio
from enum import Enum
from components import Component
import logging
import time

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

    def __init__(self, request_type: str, component: str, body=None):
        logger.debug(f"{component} - {request_type} - Initiating Request.")
        if request_type in ["SetParameters", "GetParameters"]:
            body_encode = Component('param', component, data=body).to_req()
        elif request_type in ["ChangeState", "GetState"]:
            body_encode = Component('state', component, data=body).to_req()
        else:
            logger.error(f"Unsupported Request Type {request_type}")
        self.request_type = RequestType[request_type].value.to_bytes(2, 'little')
        self.component = component
        self.body = body_encode.SerializeToString()
        logger.debug(f" request - {self.request_type} - Req Serialized to String")

    async def send(self, context=None):
        multi_msg = [DECIDE_VERSION, self.request_type, self.body]
        if self.component is not None:
            multi_msg.append(self.component.encode('utf-8'))

        ctx = context or zmq.asyncio.Context.instance()
        req_sock = ctx.socket(zmq.REQ)
        req_sock.connect(REQ_ENDPOINT)
        logger.debug(f" request - {self.request_type} - Request Socket Created")
        await req_sock.send_multipart(multi_msg)
        logger.debug(f" request - {self.request_type} - Request sent, awaiting reply")

        if req_sock.poll(TIMEOUT) == zmq.POLLIN:
            *dc, reply = req_sock.recv_multipart()
            logger.debug(f" request - {self.request_type} - Reply received '{reply.decode('utf-8')}'")
            if dc[0] != DECIDE_VERSION:
                logger.warning(f"Mismatch Version of DECIDE-RS {dc[0]}")
            return reply
        else:  # timeout awaiting response
            logger.error(f"Timed-out awaiting response for {self.request_type}")

    async def send_and_wait(self, timeout=100):
        try:
            async with asyncio.timeout(timeout):
                reply = await self.send()
        except TimeoutError:
            logger.error("Timed out awaiting response from decide-rs")
        return reply


# Await state change from component with optional timeout
# If caught returns True, immediately go to advance
# If timeout, also go to advance
async def catch(components, caught, advance, timeout=None, **kwargs):
    ctx = kwargs['context'] or zmq.asyncio.Context.instance()
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

    def test(polt, func):
        while True:
            poll_res = dict(await polt.poll())
            for sock, flag in poll_res:
                if flag == zmq.POLLIN:
                    *topic, msg = sock.recv_multipart(zmq.DONTWAIT)
                    state, comp = topic[0].decode("utf-8").split("/")
                    tstamp, state_msg = Component(state, comp).from_pub(msg)
                    if func(state_msg):
                        timed = time.time()
                        return True, timed

    if timeout is not None:
        start = time.time()
        try:
            async with asyncio.timeout(timeout):
                interrupted, stop = test(poller, caught)
                timer = stop - start
        except TimeoutError:
            timer = timeout
    else:
        timer = None
        interrupted = test(poller, caught)

    advance(interrupted, timer, **kwargs)

