import asyncio

async def timer():
    yield 1
    await asyncio.sleep(1)
    yield 3
    await asyncio.sleep(2)


class Nana:

    def __init__(self) -> None:
        self.in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue()


        self.critical_error = None
        self.recovering = False

    async def send(self, i):
        assert not self.critical_error, "Contract was broken because pod is critically errored. All requests will be cancelled"

        if self.recovering:
            print("Pod seems to be recovering... We are queing our requests. Just in case")
            await self.out_queue.put(i)

        print("Sending requests outward")

    async def worker(self):
        await asyncio.sleep(1)
        if self.contract_started:
            self.contract_started.set_result("X")
        await asyncio.sleep(1)
        self.is_running = False

    async def __aenter__(self):
        self.is_running = True
        self.loop = asyncio.get_event_loop()
        self.worker_task = self.loop.create_task(self.worker())
        self.worker_task.add_done_callback()


        self.contract_started = self.loop.create_future()
        await self.contract_started
        print("Contract is fine, starting context")
        return self

    async def __aexit__(self, *args, **kwargs):
        if not self.worker_task.done():
            self.worker_task.cancel()

async def test():
    async with Nana() as na:
        print("Starting to send")
        await na.send(4)
        await asyncio.sleep(3)
        await na.send(3)


asyncio.run(test())
