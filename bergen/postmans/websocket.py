from bergen.messages.provision_request import ProvisionRequestMessage
from bergen.utils import expandOutputs, shrinkInputs
from bergen.messages.assignation import AssignationMessage
from bergen.messages.exceptions.base import ExceptionMessage
from bergen.messages.types import ASSIGNATION, EXCEPTION
from bergen.messages.base import MessageModel
from bergen.messages.assignation_request import AssignationRequestMessage
from bergen.postmans.base import BasePostman
from aiostream import stream
import json
import uuid
import logging
import asyncio
import websockets
import sys
from bergen.schema import AssignationStatus



logger = logging.getLogger(__name__)






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
        self.futures = {}

        self.configured = False
        self.consumer_task = None
        self.producer_task = None

        self.assign_routing = "assignation_request"
        self.active_stream_queues = {}
        super().__init__(**kwargs)

    async def configure(self):
        self.callback_queue = asyncio.Queue()
        self.progress_queue = asyncio.Queue()
        self.startup_task = asyncio.create_task(self.startup())


    async def disconnect(self):
        if self.startup_task: self.startup_task.cancel()
        if self.consumer_task: self.consumer_task.cancel()
        if self.producer_task: self.producer_task.cancel()
        print("Bergen disconnected")

    async def startup(self):

        await self.connect_websocket()

        self.consumer_task = asyncio.create_task(
            self.producer()
        )
        self.producer_task = asyncio.create_task(
            self.workers()
        )

        done, pending = await asyncio.wait(
            [self.consumer_task, self.producer_task],
            return_when=asyncio.ALL_COMPLETED
        )

        for task in pending:
            task.cancel()


    async def connect_websocket(self):
        uri = f"ws://{self.host}:{self.port}/postman/?token={self.token}"
        try:
            self.connection = await websockets.client.connect(uri)
        except ConnectionRefusedError:
            sys.exit('error: cannot connect to backend')


    async def producer(self):
        logger.info(" [x] Awaiting Reponse from Postman")
        async for message in self.connection:
            await self.callback_queue.put(message)
        # await self.send_queue.put(message)

    async def workers(self):
        while True:
            message = await self.callback_queue.get()
            try:
                parsed_message = MessageModel.from_channels(message=message)

                # Stream Path
            
                if parsed_message.meta.type == EXCEPTION:
                    parsed_exception = ExceptionMessage.from_channels(message=message)
                    future = self.futures.pop(parsed_exception.data.reference)
                    future.set_exception(Exception(parsed_exception.data.message))


                if parsed_message.meta.type == ASSIGNATION:
                    parsed_assignation = AssignationMessage.from_channels(message=message)

                    correlation_id = parsed_assignation.data.reference

                    if correlation_id in self.active_stream_queues:
                        await self.active_stream_queues[correlation_id].put(parsed_assignation)
                    
                    if correlation_id in self.futures:
                        future = self.futures.pop(correlation_id)
                        future.set_result(parsed_assignation.data.outputs)

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


    async def send_to_arnheim(self,request):
        if self.connection:
            await self.connection.send(request.to_channels())
        else:
            raise Exception("No longer connected. Did you use an Async context manager?")


    async def assign(self, node, inputs, params, **extensions):
        correlation_id = str(uuid.uuid4()) # Where should we do this?
        future = self.loop.create_future()
        self.futures[correlation_id] = future

        assigned_inputs = await shrinkInputs(node=node, inputs=inputs)
       

        request = AssignationRequestMessage(data={
                                                "node":node.id, 
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
            
        outputs = await future
        return await expandOutputs(node, outputs)


    async def provide(self, node, params, **extensions):
        correlation_id = str(uuid.uuid4()) # Where should we do this?
        future = self.loop.create_future()
        self.futures[correlation_id] = future

       

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
            
        return await future


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
