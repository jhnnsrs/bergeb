from asyncio.tasks import ensure_future
from bergen.messages.provision_request import ProvisionRequestMessage
from bergen.utils import expandOutputs, shrinkInputs
from bergen.messages.assignation import AssignationMessage
from bergen.messages.provision import ProvisionMessage
from bergen.messages.exceptions.base import ExceptionMessage
from bergen.messages.types import ASSIGNATION, EXCEPTION, PROVISION
from bergen.messages.base import MessageModel
from bergen.messages.assignation_request import AssignationAction, AssignationRequestMessage
from bergen.postmans.base import BasePostman
from aiostream import stream
import json
import uuid
import logging
from functools import partial

import asyncio
try:
    from asyncio import create_task
except ImportError:
    #python 3.6 fix
    create_task = asyncio.ensure_future


import websockets
import sys
from bergen.schema import AssignationStatus
from bergen.models import Pod



logger = logging.getLogger(__name__)


class NodeException(Exception):
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
        self.futures = {}
        self.progresses = {}

        # Retry logic
        self.allowed_retries = 2
        self.current_retries = 0


        self.provision_futures = {}
        self.unprovision_futures = {}

        self.configured = False
        self.consumer_task = None
        self.producer_task = None
        self.sending_task = None

        self.assign_routing = "assignation_request"
        self.active_stream_queues = {}
        super().__init__(**kwargs)

    async def configure(self):
        self.callback_queue = asyncio.Queue()
        self.progress_queue = asyncio.Queue()

        self.send_queue = asyncio.Queue()
        self.tasks = []
        self.startup_task = create_task(self.startup())


    async def disconnect(self):
        for task in self.tasks:
            task.cancel()
        if self.startup_task: self.startup_task.cancel()
        if self.consumer_task: self.consumer_task.cancel()
        if self.producer_task: self.producer_task.cancel()
        if self.sending_task: self.sending_task.cancel()
        logger.info("Postman disconnected")

    async def startup(self):
        try:
            await self.connect_websocket()
        except Exception as e:
            logger.info(e)
            self.current_retries += 1
            if self.current_retries < self.allowed_retries:
                sleeping_time = (self.current_retries + 1)
                logger.error(f"Initial Connection failing: Trying again in {sleeping_time} seconds {e}")
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


        self.producer_task = create_task(
            self.workers()
        )

        done, pending = await asyncio.wait(
            [self.producer_task, self.receiving_task, self.sending_task],
            return_when=asyncio.FIRST_EXCEPTION
        )

        logger.error(f"Lost connection inbetween everything :( {[ task.exception() for task in done]}")
        logger.error(f'Reconnecting to {self.uri}')

        for task in pending:
            task.cancel()

        self.current_retries = 0 # reset retries after one successfull connection
        await self.startup()


    async def connect_websocket(self):
        self.connection = await websockets.client.connect(self.uri)
        

    async def receiving(self):
        logger.info(" [x] Awaiting Reponse from Postman")
        async for message in self.connection:
            await self.callback_queue.put(message)
    

    async def sending(self):
        while True:
            message = await self.send_queue.get()
            if self.connection:
                await self.connection.send(message.to_channels())
            else:
                raise Exception("No longer connected. Did you use an Async context manager?")


    async def workers(self):
        while True:
            message = await self.callback_queue.get()
            try:
                parsed_message = MessageModel.from_channels(message=message)
                # Stream Path
            
                if parsed_message.meta.type == EXCEPTION: #Protocol Exception
                    parsed_exception = ExceptionMessage.from_channels(message=message)
                    future = self.futures.pop(parsed_exception.meta.reference)
                    future.set_exception(Exception(parsed_exception.data.message))


                elif parsed_message.meta.type == ASSIGNATION: # Assignation Exception
                    parsed_assignation = AssignationMessage.from_channels(message=message)

                    correlation_id = parsed_assignation.data.reference

                    if correlation_id in self.active_stream_queues: # It is a stream delage to stream
                        await self.active_stream_queues[correlation_id].put(parsed_assignation)
                    
                    if correlation_id in self.futures:

                        if parsed_assignation.data.status == AssignationStatus.PROGRESS:
                            if correlation_id in self.progresses:
                                self.progresses[correlation_id](parsed_assignation.data.statusmessage) # call the function that is the progress function

                        if parsed_assignation.data.status == AssignationStatus.DONE:
                            if correlation_id in self.progresses:
                                self.progresses.pop(correlation_id)
                            future = self.futures.pop(correlation_id)
                            future.set_result(parsed_assignation.data.outputs)

                        if parsed_assignation.data.status == AssignationStatus.ERROR:
                            if correlation_id in self.progresses:
                                self.progresses.pop(correlation_id)
                            future = self.futures.pop(correlation_id)
                            future.set_exception(NodeException(parsed_assignation.data.statusmessage))

                elif parsed_message.meta.type == PROVISION:
                    print(message)
                    parsed_provision = ProvisionMessage.from_channels(message=message)

                    correlation_id = parsed_provision.meta.reference

                    if correlation_id in self.active_stream_queues:
                        await self.active_stream_queues[correlation_id].put(parsed_provision)
                    
                    if correlation_id in self.provision_futures:
                        future = self.provision_futures.pop(correlation_id)
                        future.set_result(parsed_provision.data.pod)

                else:
                    raise Exception("Received something weird", parsed_message )

            except Exception as e:
                logger.error(e)
            self.callback_queue.task_done()

    async def stream(self, node, inputs, params, **extensions):
        logger.info(f"Creating a Stream of Data for {node.id}")
        correlation_id = str(uuid.uuid4())

        assigned_inputs = await shrinkInputs(node=node, inputs=inputs)

        self.active_stream_queues[correlation_id] = asyncio.Queue()

        request = AssignationRequestMessage(data={
                                                "node":node.id, 
                                                "inputs": assigned_inputs, 
                                                "params": dict(params or {}),
                                                "reference": correlation_id,
                                                # We omit sending a callback
                                            },
                                            meta={
                                                "reference": correlation_id,
                                                "auth": {
                                                    "token": self.token
                                                },
                                                "extensions": extensions
                                            })

        await self.send_to_arnheim(request)

        while True:
            messagein_stream = await self.active_stream_queues[correlation_id].get()

            if messagein_stream.data.status == AssignationStatus.YIELD:
                yield await expandOutputs(node, outputs=messagein_stream.data.outputs)

            if messagein_stream.data.status == AssignationStatus.DONE:
                break


    async def stream_progress(self, node, inputs, params, **extensions):
        logger.debug(f"Creating a Stream of Progress for {node.id}")
        correlation_id = str(uuid.uuid4())

        assigned_inputs = await shrinkInputs(node=node, inputs=inputs)

        self.active_stream_queues[correlation_id] = asyncio.Queue()

        request = AssignationRequestMessage(data={
                                                "node":node.id, 
                                                "inputs": assigned_inputs, 
                                                "params": dict(params or {}),
                                                "reference": correlation_id,
                                                # We omit sending a callback
                                            },
                                            meta={
                                                "reference": correlation_id,
                                                "auth": {
                                                    "token": self.token
                                                },
                                                "extensions": {
                                                    "with_progress": True,
                                                    **extensions
                                                }
                                            })

        await self.send_to_arnheim(request)

        while True:
            messagein_stream = await self.active_stream_queues[correlation_id].get()
            if messagein_stream.data.status == AssignationStatus.PROGRESS:
                yield messagein_stream.data.statusmessage

            if messagein_stream.data.status == AssignationStatus.ERROR:
                raise NodeException(messagein_stream.data.statusmessage)

            if messagein_stream.data.status == AssignationStatus.DONE:
                yield messagein_stream.data.outputs
                break




    async def send_to_arnheim(self,request):
        await self.send_queue.put(request)

    async def assign(self, node_or_pod, inputs, params, **extensions):
        correlation_id = str(uuid.uuid4()) # Where should we do this?
        future = self.loop.create_future()

        self.futures[correlation_id] = future
        
        if "with_progress" in extensions:
            self.progresses[correlation_id] = lambda progress: logger.info(progress) # lets look for progress?


        assigned_inputs = await shrinkInputs(node=node_or_pod, inputs=inputs)

       
        #TODO: Implement assigning to pod directly
        request = AssignationRequestMessage(data={
                                                "node":node_or_pod.id, 
                                                "inputs": assigned_inputs, 
                                                "params": dict(params or {}),
                                                "reference": correlation_id,
                                                "callback": None,
                                                "progress": None,
                                            },
                                            meta={
                                                "reference": correlation_id,
                                                "auth": {
                                                    "token": self.token
                                                },
                                                "extensions": extensions
                                            })


        await self.send_to_arnheim(request)



        future.add_done_callback(partial(self.check_if_cancelled, request))  

        outputs = await future

        return await expandOutputs(node_or_pod, outputs)


    def check_if_cancelled(self, request: AssignationRequestMessage, future):
        # We cancelled the future and now would like to cancel it also on the Arnheim side
        if future.cancelled():
            request.data.action = AssignationAction.CANCEL
            self.tasks.append(asyncio.create_task(self.send_to_arnheim(request)))
            logger.warn(f"Cancelling Assignation {request.data.reference}")


    async def provide(self, node, params, **extensions):
        correlation_id = str(uuid.uuid4()) # Where should we do this?
        future = self.loop.create_future()
        self.provision_futures[correlation_id] = future

        request = ProvisionRequestMessage(data={
                                                "node":node.id, 
                                                "params": dict(params or {}),
                                                "reference": correlation_id,
                                            },
                                            meta={
                                                "reference": correlation_id,
                                                "auth": {
                                                    "token": self.token
                                                },
                                                "extensions": extensions
                                            })


        await self.send_to_arnheim(request)
            

        pod_id = await future
        pod = await Pod.asyncs.get(id=pod_id)
        return pod


    async def unprovide(self, pod):
        correlation_id = str(uuid.uuid4()) # Where should we do this?
        #future = self.loop.create_future()
        #self.unprovision_futures[correlation_id] = future

        print("Unproviding not implememted yet")           

        return False


    async def delay(self, node, inputs, params, **extensions):
        
        reference = str(uuid.uuid4())
        assigned_inputs = await shrinkInputs(node=node, inputs=inputs)
        request = AssignationRequestMessage(data={
                                                "node":node.id, 
                                                "inputs": assigned_inputs, 
                                                "params": dict(params or {}),
                                                "reference": reference,
                                                # We omit sending a callback
                                            },
                                            meta={
                                                "auth": {
                                                    "token": self.token
                                                },
                                                "extensions": extensions
                                            })

        await self.send_to_arnheim(request)

        return reference
