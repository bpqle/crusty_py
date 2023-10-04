# Simple zmq async pattern for reference

import asyncio
import random
import zmq
import zmq.asyncio
from zmq.utils import monitor
from zmq.utils.monitor import recv_monitor_message


async def main():
    b = asyncio.create_task(back())
    a = asyncio.create_task(forth())
    await asyncio.gather(a, b)

async def back():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    while True:
        socket.send_string("Hi there")
        print(f'message sent')
        await asyncio.sleep(2)

async def forth():
    context = zmq.Context()
    socket1 = context.socket(zmq.SUB)
    socket1.connect("tcp://localhost:5555")
    socket2 = context.socket(zmq.SUB)
    socket2.connect("tcp://localhost:5555")

    async def catch(soc, num):
        while True:
            soc.subscribe("")
            await asyncio.sleep(0.01)
            if soc.poll(timeout=10):
                res = soc.recv_multipart()
                print(f"{res} at {num}")
                soc.unsubscribe("")

    await asyncio.gather(catch(socket1,1), catch(socket2,2))

asyncio.run(main())