import asyncio
import time
import random
import zmq
import zmq.asyncio


async def back():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    i=0
    while True:
        topic = random.randrange(1, 3)
        socket.send_string(f"{topic} {i}")
        print(f'message sent with {topic}')
        await asyncio.sleep(3)
        i += 1


async def forth():
    context = zmq.Context()
    socket1 = context.socket(zmq.SUB)
    socket1.connect("tcp://localhost:5555")
    socket2 = context.socket(zmq.SUB)
    socket2.connect("tcp://localhost:5555")

    poller = zmq.asyncio.Poller()
    socket1.subscribe("1")
    socket2.subscribe("2")

    poller.register(socket1, zmq.POLLIN)
    poller.register(socket2, zmq.POLLIN)

    while True:
        #print("Awaiting poll")
        poll_res = await poller.poll(timeout=1000)  # ms
        print(poll_res)
        if poller,pollin
        await asyncio.sleep(1)


async def main():
    b = asyncio.create_task(back())
    a = asyncio.create_task(forth())
    await asyncio.gather(a, b)


asyncio.run(main())