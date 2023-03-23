import socket
import sys
sys.path.insert(0, '')
import zmq
import asyncio
import zmq.asyncio
import logging

import protos.house_light_pb2 as hl_proto

REQ_ENDPOINT = "tcp://127.0.0.1:7897"
PUB_ENDPOINT = "tcp://127.0.0.1:7898"

ctx = zmq.asyncio.Context()
msg = hl_proto.State()


async def recv_and_process():
    sock = ctx.socket(zmq.PULL)
    sock.bind(REQ_ENDPOINT)
    encoded_msg = await sock.recv_multipart()
    msg.ParseFromString(encoded_msg)
    reply = msg.SerializeToString()
    await sock.send_multipart(reply)

async def comp_subscribe():
    sock = ctx.socket(zmq.SUBSCRIBE)
    sock.subscribe("")
    sock.bind(PUB_ENDPOINT)
    logging.info("Begin subscription for component state changes")
    while True:
        encoded_msg = sock.recv_string()
