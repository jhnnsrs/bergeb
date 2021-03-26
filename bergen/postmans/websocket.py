from asyncio.tasks import ensure_future
from bergen.messages.postman.reserve.reserve_done import ReserveDoneMessage
from bergen.messages.postman.assign.assign_yield import AssignYieldsMessage
from bergen.messages.postman.assign.assign_critical import AssignCriticalMessage
from bergen.messages.postman.assign import AssignReturnMessage, AssignProgressMessage, CancelAssignMessage, AssignMessage
from bergen.messages.utils import expandToMessage
from bergen.messages.postman.provide import UnProvideMessage, ProvideDoneMessage, ProvideMessage,  ProvideProgressMessage, ProvideCriticalMessage
from bergen.messages.postman.reserve import ReserveMessage, CancelReserveMessage, UnReserveMessage, ReserveProgressMessage, ReserveCriticalMessage
from typing import Callable
from bergen.utils import expandOutputs, shrinkInputs
from bergen.messages.exception import ExceptionMessage
from bergen.messages.base import MessageModel
from bergen.postmans.base import BasePostman
import uuid
import logging
from functools import partial
import json

import asyncio
try:
    from asyncio import create_task
except ImportError:
    #python 3.6 fix
    create_task = asyncio.ensure_future


import websockets
from bergen.schema import AssignationStatus, Node, ProvisionStatus, Template
from bergen.models import Pod



logger = logging.getLogger(__name__)


class NodeException(Exception):
    pass

class PodException(Exception):
    pass

class ProviderException(Exception):
    pass


class Channel:

    def __init__(self, queue) -> None:
        self.queue = queue
        pass



class WebsocketPostman(BasePostman):
    type = "websocket"

    def __init__(self, port= None, protocol = None, host= None, auth= None, **kwargs) -> None:
        self.token = auth["token"]
        self.port = port
        self.protocol = protocol
        self.host = host
        self.connection = None      
        self.channel = None         
        self.callback_queue = ''

        self.uri = f"ws://{self.host}:{self.port}/postman/?token={self.token}"
        self.progresses = {}

        # Retry logic
        self.allowed_retries = 2
        self.current_retries = 0

        # Result and Stream Function
        self.futures = {}
        self.streams = {}   # Are queues that are consumed by tasks
        
        # Progress
        self.progresses = {}  # Also queues
        self.pending = []


        self.assign_routing = "assignation_request"
        super().__init__(**kwargs)

    async def connect(self):
        self.callback_queue = asyncio.Queue()
        self.progress_queue = asyncio.Queue()
        self.send_queue = asyncio.Queue()


        self.tasks = []

        self.startup_task = create_task(self.startup())


    async def disconnect(self):

        for task in self.pending:
            task.cancel()

        if self.connection: await self.connection.close()
        if self.receiving_task: self.receiving_task.cancel()
        if self.sending_task: self.sending_task.cancel()
        if self.callback_task: self.callback_task.cancel()

        if self.startup_task:
            self.startup_task.cancel()

        try:
            await self.startup_task
        except asyncio.CancelledError:
            logger.info("Postman disconnected")

    async def startup(self):
        try:
            await self.connect_websocket()
        except Exception as e:
            logger.debug(e)
            self.current_retries += 1
            if self.current_retries < self.allowed_retries:
                sleeping_time = (self.current_retries + 1)
                logger.error(f"Connection to Arkitekt Failed: Trying again in {sleeping_time} seconds.")
                await asyncio.sleep(sleeping_time)
                await self.startup()
            else:
                return

        self.receiving_task = create_task(
            self.receiving()
        )

        self.sending_task = create_task(
            self.sending()
        )

        self.callback_task = create_task(
            self.callbacks()
        )


        done, self.pending = await asyncio.wait(
            [self.callback_task, self.receiving_task, self.sending_task],
            return_when=asyncio.FIRST_EXCEPTION
        )

        logger.debug(f"Postman: Lost connection inbetween everything :( {[ task.exception() for task in done]}")
        logger.error(f'Postman: Trying to reconnect Postman')


        if self.connection: await self.connection.close()

        for task in self.pending:
            task.cancel()

        self.current_retries = 0 # reset retries after one successfull connection
        await self.startup()


    async def connect_websocket(self):
        self.connection = await websockets.client.connect(self.uri)
        logger.info("Successfully connected Postman")
        

    async def receiving(self):
        async for message in self.connection:
            await self.callback_queue.put(message)
    
    async def sending(self):
        while True:
            message = await self.send_queue.get()
            if self.connection:
                await self.connection.send(message.to_channels())
            else:
                raise Exception("No longer connected. Did you use an Async context manager?")

            self.send_queue.task_done()

    async def callbacks(self):
        while True:
            message = await self.callback_queue.get()
            logger.info(f"Received message {message}")
            try:
                parsed_message = expandToMessage(json.loads(message))
                correlation_id = parsed_message.meta.reference
                assert correlation_id in self.futures or correlation_id in self.streams , f"Received Message that wasn't originaing from our futures or streams {correlation_id}"
               
                # Stream Path

                if correlation_id in self.streams:
                    # It is a stream delage to stream
                    await self.streams[correlation_id].put(parsed_message)


                # Callback Path
                elif correlation_id in self.futures:
            
                    if isinstance(parsed_message, ExceptionMessage):
                        future = self.futures.pop(parsed_message.meta.reference)
                        future.set_exception(parsed_message.toException())

                    elif isinstance(parsed_message, AssignReturnMessage):
                        future = self.futures.pop(correlation_id)
                        future.set_result(parsed_message.data.returns)

                    elif isinstance(parsed_message, AssignProgressMessage):
                        if correlation_id in self.progresses:
                            self.progresses[correlation_id](parsed_message.data.message) 

                    elif isinstance(parsed_message, AssignCriticalMessage):
                        future = self.futures.pop(correlation_id)
                        future.set_exception(NodeException(parsed_message.data.message))

                    elif isinstance(parsed_message, ProvideDoneMessage):
                        future = self.futures.pop(correlation_id)
                        future.set_result(parsed_message.data.pod)

                    elif isinstance(parsed_message, ReserveDoneMessage):
                        future = self.futures.pop(correlation_id)
                        future.set_result((parsed_message.meta.reference, parsed_message.data.channel))

                    elif isinstance(parsed_message, ProvideCriticalMessage):
                        future = self.futures.pop(correlation_id)
                        future.set_exception(ProviderException(parsed_message.data.message))

                    elif isinstance(parsed_message, ProvideProgressMessage):
                        if correlation_id in self.progresses:
                            self.progresses[correlation_id](parsed_message.data.message) # call the function that is the progress function
 

                    else:
                        raise Exception("Unknown message type", parsed_message )


                else:
                    raise Exception("Message not in correlation_id", parsed_message )

            except Exception as e:
                logger.error(e)

            self.callback_queue.task_done()


    async def buildAssignMessage(self, reference: str = None, node: Node = None, pod: Pod = None, reservation: str = None, args=None, kwargs = None, params= None, with_progress=False):
        assert reference is not None, "Must have a reference"

        logger.info(args, kwargs)
        try:
            args, kwargs = await shrinkInputs(node=node, args=args, kwargs=kwargs)
        except Exception as e:
            logger.error(e)
        assign =  AssignMessage(data={
                                    "node": node.id if node else None, 
                                    "pod": pod.id if pod else None, 
                                    "reservation": reservation,
                                    "args": args, 
                                    "kwargs": kwargs,
                                    "params": dict(params or {}),
                                },
                                meta={
                                    "reference": reference,
                                    "extensions": {
                                        "progress": reference if with_progress else None,
                                        "callback": reference
                                    }
                                })
        logger.info(assign)
        print(assign)
        return assign


    async def stream(self, node: Node = None, pod: Pod = None, reservation: str = None, args = None, kwargs = None, params= None, on_progress: Callable = None):
        
        reference = str(uuid.uuid4())
        logger.info(f"Creating a Stream {reference}")
        self.streams[reference] = asyncio.Queue()

        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            with_progress = True
        
        assign = await self.buildAssignMessage(reference=reference, node=node, pod=pod, reservation=reservation, args=args, kwargs=kwargs, params=params, with_progress=with_progress)
        await self.send_to_arkitekt(assign)

        while True:
            parsed_message = await self.streams[reference].get()

            if isinstance(parsed_message, ExceptionMessage):
                raise parsed_message.toException()

            if isinstance(parsed_message, AssignProgressMessage):
                if on_progress:
                    asyncio.get_event_loop().call_soon_threadsafe(on_progress(parsed_message.data.message))

            if isinstance(parsed_message, AssignYieldsMessage):
                yield await expandOutputs(node, outputs=parsed_message.data.yields)

            if isinstance(parsed_message, AssignReturnMessage):
                break


        

    async def send_to_arkitekt(self,request: MessageModel):
        await self.send_queue.put(request)

    async def assign(self, node: Node = None, pod: Pod = None, reservation: str = None, args = None, kwargs = None, params= None, on_progress: Callable = None):
        reference = str(uuid.uuid4()) 
        # Where should we do this?
        future = self.loop.create_future()
        self.futures[reference] = future

        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            self.progresses[reference] = lambda progress: logger.info(progress) 
            with_progress = True
        
        assign = await self.buildAssignMessage(reference=reference, node=node, pod=pod, reservation=reservation, args=args, kwargs=kwargs, params=params, with_progress=with_progress)
        await self.send_to_arkitekt(assign)
        logger.warn(assign)

        future.add_done_callback(partial(self.check_if_assign_cancel, reference))  
        outputs = await future

        return await expandOutputs(node, outputs)


    def check_if_assign_cancel(self, reference, future):
        # We cancelled the future and now would like to cancel it also on the Arnheim side
        if future.cancelled():
            cancel = CancelAssignMessage(data={reference: reference}, meta={reference: reference})
            self.tasks.append(asyncio.create_task(self.send_to_arkitekt(cancel)))
            logger.warn(f"Cancelling Assignation {cancel.data.reference}")

        if future.exception():
            raise future.exception()

    def check_if_provide_cancel(self, reference, future):
        # We cancelled the future and now would like to cancel it also on the Arnheim side
        if future.cancelled():
            cancel = CancelAssignMessage(data={reference: reference}, meta={reference: reference})
            self.tasks.append(asyncio.create_task(self.send_to_arkitekt(cancel)))
            logger.warn(f"Cancelling Assignation {cancel.data.reference}")

        if future.exception():
            raise future.exception()


    def check_if_reserve_cancel(self, reference, future):
        # We cancelled the future and now would like to cancel it also on the Arnheim side
        if future.cancelled():
            cancel = CancelReserveMessage(data={reference: reference}, meta={reference: reference})
            self.tasks.append(asyncio.create_task(self.send_to_arkitekt(cancel)))
            logger.warn(f"Cancelling Reservation {cancel.data.reference}")

        if future.exception():
            raise future.exception()


    async def buildProvideMessage(self, reference: str = None, node: Node = None, template: Template = None, params= None, with_progress=False):
        assert reference is not None, "Must have a reference"

        return ProvideMessage(data={
                                    "node": node.id if node else None, 
                                    "template": template.id if template else None, 
                                    "params": dict(params or {}),
                                },
                                meta={
                                    "reference": reference,
                                    "extensions": {
                                        "progress": reference if with_progress else None,
                                        "callback": reference
                                    }
      
                                })

    async def buildReserveMessage(self, reference: str = None, node: Node = None, template: Template = None, params= None, with_progress=False):
        assert reference is not None, "Must have a reference"

        return ReserveMessage(data={
                                    "node": node.id if node else None, 
                                    "template": template.id if template else None, 
                                    "params": dict(params or {}),
                                },
                                meta={
                                    "reference": reference,
                                    "extensions": {
                                        "progress": reference if with_progress else None,
                                        "callback": reference
                                    }
      
                                })



    async def buildUnProvideMessage(self, reference: str = None, pod: Pod = None,  with_progress=False):
        assert pod is not None, "Must have a pod to unprovide"

        return UnProvideMessage(data={
                                    "pod": pod.id , 
                                },
                                meta={
                                    "reference": reference,
                                    "extensions": {
                                        "progress": reference if with_progress else None,
                                        "callback": reference
                                    }

                                })


    async def buildUnReserveMessage(self, reference: str = None, reservation: str = None,  with_progress=False):
        assert reservation is not None, "Must have a reservation to unreserve"

        return UnReserveMessage(data={
                                    "reservation": reservation , 
                                },
                                meta={
                                    "reference": reference,
                                    "extensions": {
                                        "progress": reference if with_progress else None,
                                        "callback": reference
                                    }

                                })


    async def unprovide(self, pod: Pod= None, on_progress: Callable = None) -> Pod:
        reference = str(uuid.uuid4()) 
        # Where should we do this?
        future = self.loop.create_future()
        self.futures[reference] = future

        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            self.progresses[reference] = lambda progress: logger.info(progress) 
            with_progress = True
        
        assign = await self.buildUnProvideMessage(reference=reference, pod=pod, with_progress=with_progress)
        await self.send_to_arkitekt(assign)
        result = await future
        return result


    async def provide(self, node: Node = None, template: Template = None , params= None, on_progress: Callable = None) -> Pod:
        reference = str(uuid.uuid4()) 
        # Where should we do this?
        future = self.loop.create_future()
        self.futures[reference] = future

        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            self.progresses[reference] = lambda progress: logger.info(progress) 
            with_progress = True
        
        assign = await self.buildProvideMessage(reference=reference, node=node, template=template, params=params, with_progress=with_progress)
        await self.send_to_arkitekt(assign)

        future.add_done_callback(partial(self.check_if_provide_cancel, reference))  
        id = await future

        pod = await Pod.asyncs.get(id=id)
        return pod


    async def reserve(self, node: Node = None, template: Template = None , params= None, on_progress: Callable = None) -> str:
        reference = str(uuid.uuid4()) 
        # Where should we do this?
        future = self.loop.create_future()
        self.futures[reference] = future

        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            self.progresses[reference] = lambda progress: logger.info(progress) 
            with_progress = True
        
        assign = await self.buildReserveMessage(reference=reference, node=node, template=template, params=params, with_progress=with_progress)
        await self.send_to_arkitekt(assign)

        future.add_done_callback(partial(self.check_if_reserve_cancel, reference))  
        reservation_id = await future
        return reservation_id

    async def unreserve(self, reservation: str= None, on_progress: Callable = None) -> Pod:
        reference = str(uuid.uuid4()) 
        # Where should we do this?
        future = self.loop.create_future()
        self.futures[reference] = future

        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            self.progresses[reference] = lambda progress: logger.info(progress) 
            with_progress = True
        
        assign = await self.buildUnReserveMessage(reference=reference, reservation=reservation, with_progress=with_progress)
        await self.send_to_arkitekt(assign)
        result = await future
        return result


    async def reserve_stream(self, node: Node = None, template: Template = None , params= None, on_progress: Callable = None):
        reference = str(uuid.uuid4())
        logger.info(f"Creating a Reservation Stream {reference}")

        self.streams[reference] = asyncio.Queue()

        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            with_progress = True
        
        assign = await self.buildReserveMessage(reference=reference, node=node, template=template, params=params, with_progress=with_progress)
        await self.send_to_arkitekt(assign)

        while True:
            parsed_message = await self.streams[reference].get()
            yield parsed_message