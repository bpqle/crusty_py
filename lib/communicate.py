import zmq
import zmq.asyncio
import logging
from enum import Enum
from components import Components
import google.protobuf.any_pb2 as _any
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
        topic = topic[0].decode("utf-8")
        print(f"Received Pub Event of topic {topic}")
        if "/" in topic:
            _state, component = topic.split("/")
            if component not in components:
                print(f"Received published event of unsubscribed component")
            else:
                tstamp, state_msg = Components("state", component).from_pub(msg)
                print(tstamp)
                print(state_msg)
        else:
            print(f"incomprehensible topic {topic}")


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

    def __init__(self, request_type: str, component: str, body=None):
        if request_type == "SetParameters":
            body_encode = Components('param', component, data=body).to_req()
        elif request_type == "ChangeState":
            body_encode = Components('state', component, data=body).to_req()
        else:
            print("Nonsense Request")
            body_encode = _any.Any()
        self.request_type = RequestType[request_type].value.to_bytes(2, 'little')
        self.component = component.encode('utf-8')
        self.body = body_encode.SerializeToString()

    async def send(self):
        multi_msg = [DECIDE_VERSION, self.request_type, self.body]
        if self.component is not None:
            multi_msg.append(self.component)
        ctx = zmq.asyncio.Context()
        req_sock = ctx.socket(zmq.REQ)
        req_sock.connect(REQ_ENDPOINT)
        logging.info("Request Socket created, sending msg")
        await req_sock.send_multipart(multi_msg)
        *dc, reply = await req_sock.recv_multipart()
        if dc[0] != DECIDE_VERSION:
            print("Mismatch Version of DECIDE-RS")
        else:
            return reply
