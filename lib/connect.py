import zmq
import zmq.asyncio
from enum import Enum
from components import Component
import logging

logger = logging.getLogger(__name__)
REQ_ENDPOINT = "tcp://127.0.0.1:7897"
PUB_ENDPOINT = "tcp://127.0.0.1:7898"
DECIDE_VERSION = b"DCDC01"


async def decide_poll(components=None):
    ctx = zmq.asyncio.Context()
    subsock = ctx.socket(zmq.SUB)
    logger.debug("Created decide-core subscriber")
    if components is None:
        subsock.subscribe("")
        logging.info(f"Sub Socket Created, Listening for all messages.")
    else:
        for c in components:
            topic = f"state/{c}"
            subsock.subscribe(topic.encode('utf-8'))
            logging.info(f"Sub Socket subscribed to {topic}.")
    subsock.connect(PUB_ENDPOINT)
    logging.debug(f"Sub Socket connected")

    while 1:
        multipart = await subsock.recv_multipart()
        *topic, msg = multipart
        topic = topic[0].decode("utf-8")
        logger.debug(f" state-pub - Received Pub Event of topic {topic}")
        if "/" in topic:
            _state, component = topic.split("/")
            if component not in components:
                logger.error(f" state-pub - Received published event of unsubscribed component {component}")
            else:
                logger.debug(f" state-pub - Parsing message")
                tstamp, state_msg = Component("state", component).from_pub(msg)
                logger.info(f" state-pub - Message: {state_msg} at Time: {tstamp}")
        else:
            logger.error(f" state-pub - Non-component topic {topic}")


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

    async def send(self):
        multi_msg = [DECIDE_VERSION, self.request_type, self.body]
        if self.component is not None:
            multi_msg.append(self.component.encode('utf-8'))
        ctx = zmq.asyncio.Context()
        req_sock = ctx.socket(zmq.REQ)
        req_sock.connect(REQ_ENDPOINT)
        logger.debug(f" request - {self.request_type} - Request Socket Created")
        await req_sock.send_multipart(multi_msg)
        logger.debug(f" request - {self.request_type} - Request sent, awaiting reply")
        *dc, reply = await req_sock.recv_multipart()
        logger.debug(f" request - {self.request_type} - Reply received")
        if dc[0] != DECIDE_VERSION:
            logger.warning(f"Mismatch Version of DECIDE-RS {dc[0]}")
        return reply.decode('utf-8') == "  "
