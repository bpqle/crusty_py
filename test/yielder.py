import asyncio

async def worker():
    while True:
        await asyncio.sleep(3)
        yield "Hello from worker"


async def main():
    b = worker()
    print(await b)


asyncio.run(main())