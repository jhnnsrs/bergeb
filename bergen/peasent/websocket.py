

from abc import ABC, abstractmethod
from typing import Union
from bergen.utils import ExpansionError, expandInputs
from bergen.messages.assignation import AssignationMessage
from bergen.schema import Template
from bergen.constants import OFFER_GQL, SERVE_GQL
from bergen.peasent.base import BasePeasent
import logging
import namegenerator
import asyncio
import websockets
from bergen.models import Node
import inspect
import sys

logger = logging.getLogger()

class WebsocketPeasent(BasePeasent):
    ''' Is a mixin for Our Bergen '''

    async def configure(self):
        self.incoming_queue = asyncio.Queue()
        await self.startup()
        
    async def startup(self):

        await self.connect_websocket()
        consumer_task = asyncio.create_task(
            self.producer()
        )
        producer_task = asyncio.create_task(
            self.workers()
        )

        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.ALL_COMPLETED
        )
        for task in pending:
            task.cancel()


    async def connect_websocket(self):
        uri = f"ws://localhost:8000/peasent/{self.unique_name}/?token={self.token}"
        try:
            self.connection = await websockets.client.connect(uri)
        except ConnectionRefusedError:
            sys.exit('error: cannot connect to backend')


    async def producer(self):
        logger.info(" [x] Awaiting RPC requests")
        async for message in self.connection:
            await self.incoming_queue.put(message)
        # await self.send_queue.put(message)


    async def run_and_send(self, message):
        # This will run in parallel and do whatever is needed !


        message = AssignationMessage.from_channels(message)
        result = await self.templateid_function_map[11](message)
        message.data.outputs = result
        await self.connection.send(message.to_channels())


    async def workers(self):
        while True:
            message = await self.incoming_queue.get()
            logger.info(" [0] Started Task")
            asyncio.create_task(self.run_and_send(message)) # Run in parallel
            self.incoming_queue.task_done()


    

