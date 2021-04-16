from bergen.actors.base import Actor
from bergen.handlers import *
from bergen.utils import *
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


import asyncio

class ClassicActor(Actor):
    pass


class ClassicFuncActor(ClassicActor):
    
    async def progress(self, value, percentage):
        await self._progress(value, percentage)

    async def assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args,kwargs):
        raise NotImplementedError("Please provide a func or overwrite the assign method!")

    async def _assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args, kwargs):
        result = await self.assign(assign_handler, reserve_handler, args, kwargs)
        try:
            shrinked_returns = await shrinkOutputs(self.template.node, result)
            await assign_handler.pass_result(shrinked_returns)
        except Exception as e:
            await assign_handler.pass_exception(e)


class ClassicGenActor(ClassicActor):

    async def progress(self, value, percentage):
        await self._progress(value, percentage)

    async def assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args,kwargs):
        raise NotImplementedError("This needs to be overwritten in order to work")

    async def _assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args, kwargs):
        async for result in self.assign(assign_handler, reserve_handler, args, kwargs):
            lastresult = await shrinkOutputs(self.template.node, result)
            await assign_handler.pass_yield(lastresult)

        await assign_handler.pass_done()


class ClassicThreadedFuncActor(ClassicActor):
    nworkers = 5

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.threadpool = ThreadPoolExecutor(self.nworkers)

    def progress(self, value, percentage):
        if self.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._progress(value, percentage=percentage), self.loop)
            return future.result()
        else:
            self.loop.run_until_complete(self._progress(value, percentage=percentage))

    def assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args,kwargs):
        raise NotImplementedError("")   

    async def _assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args, kwargs):
        result = await self.loop.run_in_executor(self.threadpool, self.assign, assign_handler, reserve_handler, args, kwargs)
        await assign_handler.pass_return(result)
