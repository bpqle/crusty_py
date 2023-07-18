import asyncio


async def worker():
    i = 0
    print("spawned")
    while True:
        await asyncio.sleep(1)
        yield f"Hello from worker {i}"
        i += 1


async def main():
    b = asyncio.create_task(worker())
    await asyncio.sleep(5)

    async def waiter(bee):
        async for msg in bee:
            print(msg)

    while True:
        try:
            await asyncio.wait_for(waiter(b), 2000)
        except TimeoutError:
            print("timed out")


asyncio.run(main())