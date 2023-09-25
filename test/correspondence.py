# Simple zmq async pattern for reference

import asyncio
import random
import zmq
import zmq.asyncio
from zmq.utils import monitor
from zmq.utils.monitor import recv_monitor_message


async def back():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    i = 0
    while True:
        topic = random.randrange(1, 3)
        socket.send_string(f"{topic} {i}")
        print(f'message sent with {topic}')
        await asyncio.sleep(3)
        i += 1
        if i == 3:
            break


async def forth():
    context = zmq.Context()
    socket1 = context.socket(zmq.SUB)
    socket1.connect("tcp://localhost:5555")
    m1 = socket1.get_monitor_socket()
    socket2 = context.socket(zmq.SUB)
    socket2.connect("tcp://localhost:5555")

    poller = zmq.asyncio.Poller()
    socket1.subscribe("1")
    socket2.subscribe("2")

    poller.register(socket1, zmq.POLLIN)
    poller.register(socket2, zmq.POLLIN)

    EVENT_MAP = {}
    for name in dir(zmq):
        if name.startswith('EVENT_'):
            value = getattr(zmq, name)
            EVENT_MAP[value] = name

    async def watch(m):
        while True:
            try:
                res = m.poll(timeout=100)
                if res != 0:
                    skips = 0
                    evt = {}
                    mon_evt = recv_monitor_message(m)
                    evt.update(mon_evt)
                    evt['description'] = EVENT_MAP[evt['event']]
                    print(f"Event: {evt}")
                    if evt['event'] == zmq.EVENT_MONITOR_STOPPED:
                        break
                else:
                    await asyncio.sleep(1)
            except RuntimeError as e:
                print(e)
                await asyncio.sleep(1)

    async def speak(s):
        while True:
            poll_res = await s.poll(timeout=1000)  # ms
            print(poll_res)
            await asyncio.sleep(1)

    await asyncio.gather(speak(poller), watch(m1))


async def main():
    b = asyncio.create_task(back())
    a = asyncio.create_task(forth())
    await asyncio.gather(a, b)


asyncio.run(main())