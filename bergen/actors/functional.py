from bergen.actors.base import Actor
from bergen.handlers import *
from bergen.utils import *
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from bergen.actors.utils import *

import asyncio

class FunctionalActor(Actor):
    pass


class FunctionalFuncActor(FunctionalActor):
    
    async def progress(self, value, percentage):
        await self._progress(value, percentage)

    async def assign(self, *args, **kwargs):
        raise NotImplementedError("Please provide a func or overwrite the assign method!")

    async def _assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args, kwargs):
        

        assign_handler_context.set(assign_handler)
        reserve_handler_context.set(reserve_handler)
        provide_handler_context.set(self.provide_handler)
        #
        result = await self.assign(*args, **kwargs)

        try:
            shrinked_returns = await shrinkOutputs(self.template.node, result)
            await assign_handler.pass_result(shrinked_returns)
        except Exception as e:
            await assign_handler.pass_exception(e)


class FunctionalGenActor(FunctionalActor):

    async def progress(self, value, percentage):
        await self._progress(value, percentage)

    async def assign(self,*args, **kwargs):
        raise NotImplementedError("This needs to be overwritten in order to work")

    async def _assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args, kwargs):

        assign_handler_context.set(assign_handler)
        reserve_handler_context.set(reserve_handler)
        provide_handler_context.set(self.provide_handler)

        async for result in self.assign(*args, **kwargs):
            lastresult = await shrinkOutputs(self.template.node, result)
            await assign_handler.pass_yield(lastresult)

        await assign_handler.pass_done()


class FunctionalThreadedFuncActor(FunctionalActor):
    nworkers = 5

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.threadpool = ThreadPoolExecutor(self.nworkers)

    def assign(self, *args, **kwargs):
        raise NotImplementedError("")   

    async def _assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args, kwargs):
        assign_handler_context.set(assign_handler)
        reserve_handler_context.set(reserve_handler)
        provide_handler_context.set(self.provide_handler)

        result = await self.loop.run_in_executor(self.threadpool, self.assign, *args, **kwargs)
        await assign_handler.pass_return(result)