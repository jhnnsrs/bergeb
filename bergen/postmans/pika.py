

from bergen.messages.assignation import AssignationMessage
from bergen.messages.exceptions.base import ExceptionMessage
from bergen.messages.types import ASSIGNATION, EXCEPTION
from bergen.messages.base import MessageModel
from bergen.messages.assignation_request import AssignationRequestMessage
from bergen.postmans.base import BasePostman
from aiostream import stream
import aiormq
import json
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)






class PikaPostman(BasePostman):
    type = "pika"

    def __init__(self, port= None, protocol = None, host= None, auth= None, **kwargs) -> None:
        self.token = auth["token"]
        self.port = port
        self.protocol = protocol
        self.host = host
        self.connection = None      # type: aiormq.Connection
        self.channel = None         # type: aiormq.Channel
        self.callback_queue = ''
        self.futures = {}

        self.configured = False

        self.assign_routing = "assignation_request"
        super().__init__(**kwargs)

    async def configure(self):

        self.loop = asyncio.get_event_loop()
        self.connection = await aiormq.connect(f"amqp://{self.token}:guest@{self.host}/")

        self.channel = await self.connection.channel()
        declare_ok = await self.channel.queue_declare(
            exclusive=True, auto_delete=True
        )
        declare_progress = await self.channel.queue_declare(
            exclusive=True, auto_delete=True
        )

        await self.channel.basic_consume(declare_ok.queue, self.on_response)
        await self.channel.basic_consume(declare_progress.queue, self.on_progress)

        self.callback_queue = declare_ok.queue
        self.progress_queue = declare_progress.queue

    async def on_response(self, message: aiormq.types.DeliveredMessage):
        print("Received somethign here")
        correlationid = message.header.properties.correlation_id
        if correlationid not in self.futures: 
            print("Received Uncorrelated")
            return # TODO: Handle this? We coudlnt care less

        parsed_message = MessageModel.from_message(message=message)
        future = self.futures.pop(message.header.properties.correlation_id)
        if parsed_message.meta.type == EXCEPTION:
            parsed_exception = ExceptionMessage.from_message(message=message)
            future.set_exception(Exception(parsed_exception.data.message))
        if parsed_message.meta.type == ASSIGNATION:
            parsed_assignation = AssignationMessage.from_message(message=message)
            future.set_result(parsed_assignation.data.outputs)
        else:
            raise Exception("Received something weird", message.body.decode() )

    async def on_progress(self, message: aiormq.types.DeliveredMessage):
        logger.info(message.body.decode())


    async def assign(self, node, inputs, params, **extensions):
        correlation_id = str(uuid.uuid4()) # Where should we do this?
        future = self.loop.create_future()
        self.futures[correlation_id] = future
       

        request = AssignationRequestMessage(data={
                                                "node":node.id, 
                                                "inputs": inputs or {}, 
                                                "params": dict(params or {}),
                                                "reference": correlation_id,
                                                "callback": self.callback_queue,
                                                "progress": self.progress_queue,
                                            },
                                            meta={
                                                "auth": {
                                                    "token": self.token
                                                },
                                                "extensions": extensions
                                            })
            
        await self.channel.basic_publish(
            str(json.dumps(request.dict())).encode(), routing_key=self.assign_routing,
            properties=aiormq.spec.Basic.Properties(
                content_type='application/json',
                correlation_id=correlation_id,
                reply_to=self.callback_queue, # If we have a malformed Message
            )
        )

        return await future


    async def delay(self, node, inputs, params, **extensions):
        
        reference = str(uuid.uuid4())
        
        request = AssignationRequestMessage(data={
                                                "node":node.id, 
                                                "inputs": inputs, 
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

        await self.channel.basic_publish(
            str(json.dumps(request.dict())).encode(), routing_key=self.assign_routing,
            properties=aiormq.spec.Basic.Properties(
                content_type='application/json',
                correlation_id=reference,
                reply_to=self.callback_queue, #TODO: There might be not a need for this?
            )
        )

        return reference
