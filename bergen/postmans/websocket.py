from asyncio.tasks import ensure_future

from websockets.exceptions import ConnectionClosedError
from bergen.messages import *
from bergen.messages.utils import expandToMessage 
from typing import Callable
from bergen.utils import expandOutputs, shrinkInputs
from bergen.messages.exception import ExceptionMessage
from bergen.messages.base import MessageModel
from bergen.postmans.base import BasePostman
import uuid
import logging
from functools import partial
import json
from bergen.console import console
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

    def __init__(self, client, port= None, protocol = None, host= None, auth= None, **kwargs) -> None:
        super().__init__(client, **kwargs)
        self.token = auth["token"]
        self.port = port or client.config.port
        self.protocol = protocol
        self.host = host or client.config.host
        self.connection = None      
        self.channel = None         
        self.callback_queue = ''

        self.uri = f"ws://{self.host}:{self.port}/postman/?token={self.token}"
        self.progresses = {}

        # Retry logic
        self.auto_reconnect = True
        self.current_retries = 0

        # Result and Stream Function
        self.futures = {}
        self.streams = {}   # Are queues that are consumed by tasks
        
        # Progress
        self.progresses = {}  # Also queues
        self.pending = []

        self.receiving_task = None
        self.sending_task = None
        self.callback_task = None


        self.assign_routing = "assignation_request"

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
            console.print("[green] Connection attempt as Postman failed")
            self.current_retries += 1
            self.current_retries += 1
            if self.auto_reconnect:
                sleeping_time = (self.current_retries + 1)
                console.print(f"[green] Trying to Reconnect as Postman in {sleeping_time} seconds")
                await asyncio.sleep(sleeping_time)
                await self.startup()
            else:
                return

        console.print("[green] Successfully established Postman Connection")

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

        try:
            for task in done:
                if task.exception():
                    raise task.exception()


        except ConnectionClosedError:
            console.print("[green] Postman Connection was closed. Trying Reconnect")
        except:
            console.print_exception()


        logger.debug(f"Postman: Lost connection inbetween everything :( {[ task.exception() for task in done]}")
        logger.error(f'Postman: Trying to reconnect Postman')
        

        if self.connection: await self.connection.close()

        for task in self.pending:
            task.cancel()

        self.current_retries = 0 # reset retries after one successfull connection
        await self.startup()


    async def connect_websocket(self):
        self.connection = await websockets.client.connect(self.uri)
        logger.info("Successfully connected [bold]Postman")
        

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
            try:
                parsed_message = expandToMessage(json.loads(message))
                await self.on_message(parsed_message)
            except:
                raise 

            self.callback_queue.task_done()


    async def forward(self, message: MessageModel):
        await self.send_queue.put(message)
        


