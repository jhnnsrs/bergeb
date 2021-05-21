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

    async def assign(self, assign_handler: AssignHandler, args, kwargs):
        raise NotImplementedError("Please provide a func or overwrite the assign method!")

    async def _assign(self, assign_handler: AssignHandler, args, kwargs):
        result = await self.assign(assign_handler, args, kwargs)
        try:
            shrinked_returns = await shrinkOutputs(self.template.node, result) if self.shrinkOutputs else result
            await assign_handler.pass_result(shrinked_returns)
        except Exception as e:
            await assign_handler.pass_exception(e)


class ClassicGenActor(ClassicActor):

    async def progress(self, value, percentage):
        await self._progress(value, percentage)

    async def assign(self, assign_handler: AssignHandler, args, kwargs):
        raise NotImplementedError("This needs to be overwritten in order to work")

    async def _assign(self, assign_handler: AssignHandler, args, kwargs):
        async for result in self.assign(assign_handler, args, kwargs):
            lastresult = await shrinkOutputs(self.template.node, result) if self.shrinkOutputs else result
            await assign_handler.pass_yield(lastresult)

        await assign_handler.pass_done()



