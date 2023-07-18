import asyncio

async def worker():
    i = 0
    print("spawned")
    while True:
        await asyncio.sleep(1)
        yield f"Hello from worker {i}"
        i += 1


async def main():
    b = worker()
    await asyncio.sleep(5)
    while True:
        async for msg in b:
            print(msg)


asyncio.run(main())