from bergen.actors.base import Actor
from bergen.handlers import *
from bergen.utils import *
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from bergen.actors.utils import *
import janus
import asyncio
import threading


class FunctionalActor(Actor):
    pass


class FunctionalFuncActor(FunctionalActor):
    
    async def progress(self, value, percentage):
        await self._progress(value, percentage)

    async def assign(self, *args, **kwargs):
        raise NotImplementedError("Please provide a func or overwrite the assign method!")

    async def _assign(self, assign_handler: AssignHandler, args, kwargs):
        bounce_context.set(assign_handler.message.meta.context)
        assign_handler_context.set(assign_handler)
        provide_handler_context.set(self.provide_handler)
        #
        result = await self.assign(*args, **kwargs)

        try:
            shrinked_returns = await shrinkOutputs(self.template.node, result) if self.shrinkOutputs else result
            await assign_handler.pass_return(shrinked_returns)
        except Exception as e:
            await assign_handler.pass_exception(e)


class FunctionalGenActor(FunctionalActor):

    async def progress(self, value, percentage):
        await self._progress(value, percentage)

    async def assign(self,*args, **kwargs):
        raise NotImplementedError("This needs to be overwritten in order to work")

    async def _assign(self, assign_handler: AssignHandler, args, kwargs):
        bounce_context.set(assign_handler.message.meta.context)
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


    async def iterate_queue(self, async_q, assign_handler: AssignHandler, provide_handler):
        while True:
            val = await async_q.get()
            action = val[0]
            if action == "log":
                await assign_handler.pass_log(val[1][0], level=val[1][1])
                async_q.task_done()
            if action == "return":
                await assign_handler.pass_return(val[1])
                async_q.task_done()
                break
            if action == "exception":
                await assign_handler.pass_exception(val[1])
                async_q.task_done()
                break  



    def _assign_threaded(self, args, kwargs, queue, context):
        queue_context.set(queue)
        bounce_context.set(context)
        try:
            result = self.assign(*args, **kwargs)
            lastresult = shrinkOutputsSync(self.template.node, result) if self.shrinkOutputs else result
            queue.put(("return", lastresult))
            queue.join()

        except Exception as e:
            console.print_exception()
            queue.put(("exception", e))
            queue.join()

        queue_context.set(None)
        bounce_context.set(None)


    async def _assign(self, assign_handler: AssignHandler, args, kwargs):
        queue = janus.Queue()

        try:
            threadedfut = self.loop.run_in_executor(self.threadpool, self._assign_threaded, args, kwargs, queue.sync_q, assign_handler.message.meta.context)
            queuefut =  self.iterate_queue(queue.async_q, assign_handler, self.provide_handler)

            try:
                await asyncio.gather(threadedfut, queuefut)
                queue.close()
                await queue.wait_closed()
            except asyncio.CancelledError as e:
                console.log("Received Cancellation for task")

                if not threadedfut.done():
                    print("Sending request to Queue To Cancell")
                    threadedfut.cancel()

                try:
                    await threadedfut
                except asyncio.CancelledError as e:
                    print("Sucessfully Cancelled Thread")
                    raise e

        except Exception as e:
            await assign_handler.pass_exception(e)



class FunctionalThreadedGenActor(FunctionalActor):
    nworkers = 5

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.threadpool = ThreadPoolExecutor(self.nworkers)

    def assign(self, *args, **kwargs):
        raise NotImplementedError("")  


    def _assign_threaded(self, args, kwargs, queue, event, context):
        queue_context.set(queue)
        bounce_context.set(context)
        try:
            if event.is_set(): 
                queue.put(("cancelled","Happy doneness")) 
                return

            for result in self.assign(*args, **kwargs):
                if event.is_set():
                    queue.put(("cancelled","Happy doneness"))
                    return
                    
                lastresult = shrinkOutputsSync(self.template.node, result) if self.shrinkOutputs else result
                queue.put(("yield", lastresult))
                queue.join()
        except Exception as e:
            console.print_exception()
            queue.put(("exception", e))

        queue.put(("done","Happy doneness"))
        queue_context.set(None)
        bounce_context.set(None)


    async def iterate_queue(self, async_q, assign_handler: AssignHandler, provide_handler):

        while True:
            val = await async_q.get()
            action = val[0]
            if action == "log":
                await assign_handler.pass_log(val[1][0], level=val[1][1])
                async_q.task_done()
            if action == "yield":
                await assign_handler.pass_yield(val[1])
                async_q.task_done()
            if action == "exception":
                await assign_handler.pass_exception(val[1])
                async_q.task_done()
                break
            if action == "done":
                await assign_handler.pass_done()
                async_q.task_done()
                break

        

    async def _assign(self, assign_handler: AssignHandler, args, kwargs):
        queue = janus.Queue()
        print(assign_handler.message.meta.context)

        event = threading.Event()

        try:
            threadedfut = self.loop.run_in_executor(self.threadpool, self._assign_threaded, args, kwargs, queue.sync_q, event, assign_handler.message.meta.context)
            queuefut =  self.iterate_queue(queue.async_q, assign_handler, self.provide_handler)

            try:
                await asyncio.gather(threadedfut, queuefut)
                queue.close()
                await queue.wait_closed()
            except asyncio.CancelledError as e:
                console.log("Received Cancellation for task")

                if not threadedfut.done():
                    print("Sending request to Queue To Cancell")
                    event.set()
                    threadedfut.cancel()

                try:
                    await threadedfut
                except asyncio.CancelledError as e:
                    print("Sucessfully Cancelled Thread")
                    raise e

        except Exception as e:
            await assign_handler.pass_exception(e)