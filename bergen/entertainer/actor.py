

from abc import ABC, abstractmethod
from asyncio.events import AbstractEventLoop
from asyncio.futures import Future
from re import M
from bergen.messages.postman.assign.bounced_cancel_assign import BouncedCancelAssignMessage
from bergen.messages.postman.assign.bounced_assign import BouncedAssignMessage
import contextvars
from typing import Type
from bergen.types.node.ports import kwarg
from bergen.messages.postman.assign.assign import AssignMessage
import uuid

from pydantic.main import BaseModel
from bergen.utils import expandInputs, shrinkInputs, shrinkOutputs
from bergen.schema import Template
from bergen.constants import ACCEPT_GQL, OFFER_GQL, SERVE_GQL
import logging
import asyncio
from bergen.models import Node, Pod
import inspect
from aiostream import stream
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial


logger = logging.getLogger()

class HostHelper(ABC):

    def __init__(self, host) -> None:
        self.host = host
        pass

    @abstractmethod
    async def pass_yield(self, message, value):
        pass

    @abstractmethod
    async def pass_progress(self, message, value, percentage=None):
        pass

    @abstractmethod
    async def pass_result(self, message, value):
        pass

    @abstractmethod
    async def pass_exception(self, message, exception):
        pass


assign_var = contextvars.ContextVar('assign', default=None)

class Actor:

    def __init__(self, pod: Pod, helper: HostHelper, loop=None) -> None:
        self.queue = asyncio.Queue()
        self.pod = pod
        self.helper = helper
        self.loop = loop
        self.assignments = {}
        pass

    async def on_provide(self):
        pass

    def check_if_assignation_cancelled(self, assign, future):
        print(future)

    async def run(self):
        ''' An infinitie loop assigning to itself'''
        try:
            logger.info(f"Run for {self.__class__.__name__} on Pod {self.pod.id}: Pod was Provided. Reserving")
            await self.on_provide()
            logger.info(f"Run for {self.__class__.__name__} on Pod {self.pod.id}: Resources were reservered. Waiting for Tasks until canceled")
            
            while True:
                message = await self.queue.get()
                logger.info(f"Assignation for {self.__class__.__name__} on Pod {self.pod.id}: {message}")

                if isinstance(message, BouncedAssignMessage):
                    logger.info(f"Assignation for {self.__class__.__name__} on Pod {self.pod.id}: {message}")
                    task = asyncio.create_task(self.on_assign(message))
                    task.add_done_callback(partial(self.check_if_assignation_cancelled, message))
                    self.assignments[message.meta.reference] = task

                elif isinstance(message, BouncedCancelAssignMessage):
                    logger.info(f"Assignation Cancellation for {self.__class__.__name__} on Pod {self.pod.id}: {message}")
                    if message.data.reference in self.assignments: 
                        logger.info("Cancellation for task received. Canceling!")
                        task = self.assignments[message.data.reference]
                        if not task.done():
                            task.cancel()
                            logger.warn("Canceled Task!!")
                        else:
                            logger.warn("Task had already finished")
                    else:
                        raise Exception("Assignment never was at this pod. something went wrong")

                else:
                    raise Exception(f"Type not known {message}")

                self.queue.task_done()


        except asyncio.CancelledError:
            logger.info(f"Run for {self.__class__.__name__} on Pod {self.pod.id}: Received Entertainment Cancellation. Unreserving")
            await self.on_unprovide()
            logger.info(f"Run for {self.__class__.__name__} on Pod {self.pod.id}: Unprovided. Ciao!")
            raise

        except Exception as e:
            logger.error(e)
            raise e

    async def on_unprovide(self):
        pass

    async def progress(self, value, percentage):
        message = assign_var.get()
        await self.helper.pass_progress(message, value, percentage)

    async def on_assign(self, assign: AssignMessage):
        args, kwargs = await expandInputs(node=self.pod.template.node, args=assign.data.args, kwargs=assign.data.kwargs)
        logger.info(args, kwargs)
        assign_var.set(assign)
        await self._assign(**{**args, **kwargs})
    
    async def __aenter__(self):
        await self.reserve()
        return self

    async def __aexit__(self):
        await self.unreserve()



class AsyncActor(Actor):

    def __init__(self, pod: Pod, helper: HostHelper) -> None:
        super().__init__(pod, helper)



class AsyncFuncActor(AsyncActor):

    async def assign(self, *args, **kwargs):
        raise NotImplementedError("Please provide a func or overwrite the assign method!")

    async def _assign(self, *args, **kwargs):
        message = assign_var.get()
        result = await self.assign(*args, **kwargs)
        try:
            shrinked_returns = await shrinkOutputs(self.pod.template.node, result)
            await self.helper.pass_result(message, shrinked_returns)
        except Exception as e:
            logger.error(e)
            await self.helper.pass_exception(message, e)




class AsyncGenActor(AsyncActor):

    async def assign(self):
        raise NotImplementedError("This needs to be overwritten in order to work")

    async def _assign(self, *args, **kwargs):
        message = assign_var.get()
        yieldstream = stream.iterate(self.assign(*args, **kwargs))
        async with yieldstream.stream() as streamer:
            async for result in streamer:
                lastresult = await shrinkOutputs(self.pod.template.node, result)
                await self.helper.pass_yield(message, lastresult)

        await self.helper.pass_result(message, lastresult)


class ThreadedFuncActor(Actor):
    nworkers = 5

    def __init__(self, pod: Pod, helper: HostHelper, loop) -> None:
        super().__init__(pod, helper, loop=loop)
        self.threadpool = ThreadPoolExecutor(self.nworkers)

    def progress(self, value, percentage):
        message = assign_var.get()
        logger.info(f'{percentage if percentage else "--"} : {value}')
        if self.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.helper.pass_progress(message, value, percentage=percentage), self.loop)
            return future.result()
        else:
            self.loop.run_until_complete(self.helper.pass_progress(message, value, percentage=percentage))

    def assign(self):
        raise NotImplementedError("")   

    async def _assign(self, *args, **kwargs):
        message = assign_var.get()
        result = await self.loop.run_in_executor(self.threadpool, self.assign)

        returns = await shrinkOutputs(self.pod.template.node, result)
        await self.helper.pass_result(message, returns)


