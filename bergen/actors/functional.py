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

    async def _assign(self, assign_handler: AssignHandler, args, kwargs):
    
        assign_handler_context.set(assign_handler)
        provide_handler_context.set(self.provide_handler)
        #
        result = await self.assign(*args, **kwargs)

        try:
            shrinked_returns = await shrinkOutputs(self.template.node, result) if self.shrinkOutputs else result
            await assign_handler.pass_result(shrinked_returns)
        except Exception as e:
            await assign_handler.pass_exception(e)


class FunctionalGenActor(FunctionalActor):

    async def progress(self, value, percentage):
        await self._progress(value, percentage)

    async def assign(self,*args, **kwargs):
        raise NotImplementedError("This needs to be overwritten in order to work")

    async def _assign(self, assign_handler: AssignHandler, args, kwargs):

        assign_handler_context.set(assign_handler)
        provide_handler_context.set(self.provide_handler)

        try:
            async for result in self.assign(*args, **kwargs):
                lastresult = await shrinkOutputs(self.template.node, result) if self.shrinkOutputs else result
                await assign_handler.pass_yield(lastresult)

            await assign_handler.pass_done()
        except Exception as e:
            await assign_handler.pass_exception(e)


class FunctionalThreadedFuncActor(FunctionalActor):
    nworkers = 5

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.threadpool = ThreadPoolExecutor(self.nworkers)

    def assign(self, *args, **kwargs):
        raise NotImplementedError("")   


    def _assign_threaded(self, args, kwargs, loop, assign_handler, provide_handler):
        assign_handler_context.set(assign_handler)
        provide_handler_context.set(provide_handler)
        loop_context.set(loop)
        res = self.assign(*args, **kwargs)
        loop_context.set(None)
        return res

    async def _assign(self, assign_handler: AssignHandler, args, kwargs):
        try:
            result = await self.loop.run_in_executor(self.threadpool, self._assign_threaded, args, kwargs, self.loop, assign_handler, self.provide_handler)
            shrinked_returns = await shrinkOutputs(self.template.node, result) if self.shrinkOutputs else result
            await assign_handler.pass_result(shrinked_returns)
        except Exception as e:
            await assign_handler.pass_exception(e)