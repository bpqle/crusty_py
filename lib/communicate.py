import zmq
import asyncio
import zmq.asyncio
import logging
from enum import Enum
import lib.house_light as hl_proto
import lib.peckboard as pb_proto
import lib.sound_alsa as sa_proto
import lib.stepper_motor as sm_proto

REQ_ENDPOINT = "tcp://127.0.0.1:7897"
PUB_ENDPOINT = "tcp://127.0.0.1:7898"
DECIDE_VERSION = b"DCDC01"


async def decide_poll(components=None):
    ctx = zmq.asyncio.Context()
    subsock = ctx.socket(zmq.SUB)
    if components is None:
        subsock.subscribe("")
    else:
        for c in components:
            topic = f"state/{c}"
            subsock.subscribe(topic.encode('utf-8'))
    subsock.connect(PUB_ENDPOINT)
    logging.info(f"Sub Socket Created for {components}.")

    while 1:
        multipart = await subsock.recv_multipart()
        *topic, msg = multipart
        state, comp = topic.split("/")
        print(f"Received Published Event of component {comp}")
        if comp not in components:
            logging.error(f"Received published event of unsubscribed component")
        state = parse_from_pub(comp, msg)
        print(state)


class RequestType(Enum):
    ChangeState = 0x00
    ResetState = 0x01
    SetParameters = 0x02
    GetParameters = 0x12
    ComponentShutdown = 0x13
    RequestLock = 0x20
    ReleaseLock = 0x21
    Shutdown = 0x22


def req_from_mtp(multi_msg: list[bytes]):
    if len(multi_msg) < 3:
        logging.error("Incorrect Message Length Received")
    version = multi_msg.pop(0)
    if version != DECIDE_VERSION:
        logging.warning("Different Version of Decide Message Received")
    reqtype_int = multi_msg.pop(0)[0]
    body = multi_msg.pop(0)
    component = None
    if reqtype_int > 30:  # General Request
        component = None
    elif reqtype_int < 30:  # Component Request
        component = str(multi_msg.pop(0))
    else:
        logging.error("Invalid Request Type Found")

    return Request(RequestType(reqtype_int).name, component, body)


class Request:

    def __init__(self, request_type: str, component=None, body=None):
        self.request_type = RequestType[request_type].value.to_bytes(2, 'big')
        self.component = component
        self.body = body

    async def send(self):
        multi_msg = [DECIDE_VERSION, self.request_type, self.body]
        if self.component is not None:
            multi_msg.append(self.component)
        ctx = zmq.asyncio.Context()
        req_sock = ctx.socket(zmq.REQ)
        req_sock.connect(REQ_ENDPOINT)
        logging.info("Request Socket created, sending msg")
        await req_sock.send(multi_msg)
        reply = await req_sock.recv()

        return reply


def parse_from_pub(component, msg: bytes):
    if component == 'house-light':
        state = hl_proto.HlState.parse(data=msg)
    elif component == 'peck-led':
        state = pb_proto.LedState.parse(data=msg)
    elif component == 'peck-key':
        state = pb_proto.KeyState.parse(data=msg)
    elif component == 'stepper-motor':
        state = sm_proto.SmState.parse(data=msg)
    elif component == 'sound-alsa':
        state = sa_proto.SaState.parse(data=msg)
    else:
        logging.error(f"Unknown component {component}")
        state = None
    return state
