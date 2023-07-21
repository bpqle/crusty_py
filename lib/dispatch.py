import zmq
import asyncio
import zmq.asyncio
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
        self.subber.subscribe(b"")
        self.caller = context.socket(zmq.REQ)
        self.caller.connect(REQ_ENDPOINT)

        self.queue = asyncio.Queue()
        logger.dispatch("REQ and PUB sockets created.")

    async def command(self, request_type: str, component: str, body=None, timeout=TIMEOUT):
        req = await Request.spawn(request_type, component, body)
        message = [DECIDE_VERSION, req.type_encode, req.body]
        if component is not None:
            message.append(component.encode('utf-8'))
        await self.caller.send_multipart(message)
        logger.dispatch(f"Request {request_type} - {component} sent, awaiting response")
        poll_res = await self.caller.poll(timeout=timeout)
        logger.dispatch(f"Response {request_type} - {component} received")
        if poll_res == zmq.POLLIN:
            *dc, reply = await self.caller.recv_multipart()
            logger.dispatch(f" {request_type} - {component}  Reply received '{reply}'")
            if dc[0] != DECIDE_VERSION:
                logger.warning(f"Mismatch Version of DECIDE-RS in reply {dc[0]}")

            # Parse Reply:
            rep_template = dc_db.Reply()
            rep_template.ParseFromString(reply)
            result = rep_template.WhichOneof('result')
            logger.dispatch(f" {request_type} - {component}  Reply parsed as {result}")
            if result == 'ok':
                return
            elif result == 'error':
                logger.error(f"Reply error from decide-rs: {rep_template.result}")
            elif result == 'params':  # decode params
                any_params = rep_template.params
                part = Component('param', component)
                params = await part.from_any(any_params)
                logger.dispatch(f" Response {request_type} - {component} params parsed")
                return params
        else:  # timeout awaiting response
            logger.error(f"{request_type} - {component}"
                         f" Timed out after {TIMEOUT}ms awaiting response from decide-rs")

    async def eye(self):
        logger.dispatch("Sauron's Eye watching")
        while True:
            *topic, msg = await self.subber.recv_multipart()
            state, comp = topic[0].decode("utf-8").split("/")
            logger.dispatch(f"Eye spy emitted pub message from {comp}")
            proto_comp = Component(state, comp)
            tstamp, state_msg = await proto_comp.from_pub(msg)
            decoded = MessageToDict(state_msg,
                                    including_default_value_fields=True,
                                    preserving_proto_field_name=True)
            # log event here
            await self.queue.put([comp, decoded])

    async def purge(self):
        while not self.queue.empty():
            self.queue.get_nowait()
            self.queue.task_done()

    async def scry(self, component, condition, failure=None, timeout=None):
        logger.dispatch(f"Scry process started for {component}")
        if isinstance(component, str):
            self.subber.subscribe(f"state/{component}".encode('utf-8'))

        interrupted = False
        message = None
        timer = None

        async def test(sock, func):
            logger.dispatch(f"Scry {component} - test starting")
            nonlocal interrupted, message, start, timer
            while True:
                *topic, msg = await sock.recv_multipart()
                logger.dispatch(f"Scry {component} - message received, checking")
                state, comp = topic[0].decode("utf-8").split("/")
                proto_comp = Component(state, comp)
                tstamp, state_msg = await proto_comp.from_pub(msg)
                decoded = MessageToDict(state_msg,
                                        including_default_value_fields=True,
                                        preserving_proto_field_name=True)
                logger.debug(decoded)
                if func(decoded):
                    end = time.time()
                    timer = end - start
                    message = decoded
                    interrupted = True
                    logger.dispatch(f"Scry {component} - check succeeded. Ending.")
                    return
                else:
                    logger.dispatch(f"Scry {component} - check failed. Continuing.")
                    continue

        start = time.time()
        if timeout is not None:
            try:
                await asyncio.wait_for(test(self.subber, condition), timeout)
            except asyncio.exceptions.TimeoutError:
                message = None
                timer = timeout
                if failure is not None:
                    failure(component)
        else:
            await test(self.subber, condition)

        self.subber.unsubscribe(f"state/{component}")
        logger.dispatch(f"Scry finished for {component}.")
        return interrupted, message, timer


class Request:
    @classmethod
    async def spawn(cls, request_type: str, component: str, body=None):
        self = Request()
        logger.dispatch(f"{request_type} - {component} Initiating Request.")
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
        logger.dispatch(f"{request_type} - {component} Req Serialized to String")
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