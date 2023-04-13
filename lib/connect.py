import zmq
import zmq.asyncio
from enum import Enum
from components import Components
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
            logging.info(f"Sub Socket Created, Listening for {components}.")
    subsock.connect(PUB_ENDPOINT)
    logging.debug(f"Sub Socket connected")

    while 1:
        multipart = await subsock.recv_multipart()
        *topic, msg = multipart
        topic = topic[0].decode("utf-8")
        logger.debug(f"Received Pub Event of topic {topic}")
        if "/" in topic:
            _state, component = topic.split("/")
            if component not in components:
                logger.error(f"Received published event of unsubscribed component {component}")
            else:
                logger.debug(f"Parsing message")
                tstamp, state_msg = Components("state", component).from_pub(msg)
                logger.info(f"Message: {state_msg} at Time: {tstamp}")
        else:
            logger.error(f"Non-component topic {topic}")


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
        logger.debug(f"Initiating {request_type} Req for {component}")
        if request_type in ["SetParameters", "ChangeState", "GetParameters", "GetState"]:
            body_encode = Components('param', component, data=body).to_req()
        else:
            logger.error(f"Unsupported Request Type {request_type}")
        self.request_type = RequestType[request_type].value.to_bytes(2, 'little')
        self.component = component.encode('utf-8')
        self.body = body_encode.SerializeToString()
        logger.debug(f"Request Serialized to String")

    async def send(self):
        multi_msg = [DECIDE_VERSION, self.request_type, self.body]
        if self.component is not None:
            multi_msg.append(self.component)
        ctx = zmq.asyncio.Context()
        req_sock = ctx.socket(zmq.REQ)
        req_sock.connect(REQ_ENDPOINT)
        logger.debug("Request Socket Created")
        await req_sock.send_multipart(multi_msg)
        logger.debug("Request sent, awaiting reply")
        *dc, reply = await req_sock.recv_multipart()
        logger.debug("Reply received")
        if dc[0] != DECIDE_VERSION:
            logger.warning(f"Mismatch Version of DECIDE-RS {dc[0]}")
        return reply.decode('utf-8')
