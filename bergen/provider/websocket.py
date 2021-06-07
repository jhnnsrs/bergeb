

from abc import ABC, abstractmethod
from bergen.clients.base import BaseBergen

from websockets.exceptions import ConnectionClosedError
from bergen.messages import *
from bergen.messages.utils import expandToMessage
from bergen.messages.base import MessageModel
from bergen.provider.base import BaseProvider
import logging
import asyncio
import websockets
import json
import asyncio
from bergen.console import console
try:
    from asyncio import create_task
except ImportError:
    #python 3.6 fix
    create_task = asyncio.ensure_future


logger = logging.getLogger()



DEBUG = True

class WebsocketProvider(BaseProvider):
    ''' Is a mixin for Our Bergen '''

    def __init__(self, client: BaseBergen, auto_reconnect=True, **kwargs) -> None:
        super().__init__(client, **kwargs)
        self.websocket_host = client.config.host
        self.websocket_port = client.config.port
        self.websocket_protocol = "wss" if client.config.secure else "ws"
        self.pending = None

        self.auto_reconnect = True
        self.allowed_retries = 2
        self.current_retries = 0


    async def connect(self):
        self.incoming_queue = asyncio.Queue()
        self.outgoing_queue = asyncio.Queue()


        self.tasks = {}

        self.startup_task = create_task(self.startup())


    async def disconnect(self) -> str:

        for task in self.pending:
            task.cancel()


        if self.connection: await self.connection.close()

        if self.pending:
            for task in self.pending:
                task.cancel()

            try:
                await asyncio.wait(self.pending)
            except asyncio.CancelledError:
                pass

            logger.info("Peasent disconnected")

        
    async def startup(self):
        try:
            await self.connect_websocket()
        except Exception as e:

            console.print("[blue] Connection attempt as Provider failed")
            self.current_retries += 1
            if self.auto_reconnect:
                sleeping_time = (self.current_retries + 1)
                console.print(f"[blue] Trying to Reconnect as Provider in {sleeping_time} seconds")
                await asyncio.sleep(sleeping_time)
                await self.startup()
            else:
                console.print("[blue]Provider: No reconnecting attempt envisioned. Shutting Down!")
                console.print_exception()

        console.print("[blue] Sucessfully Established A Connection to Provider Endpoint")

        self.consumer_task = create_task(
            self.consumer()
        )

        self.producer_task = create_task(
            self.producer()
        )

        self.worker_task = create_task(
            self.workers()
        )

        done, self.pending = await asyncio.wait(
            [self.consumer_task, self.worker_task, self.producer_task],
            return_when=asyncio.FIRST_EXCEPTION
        )

        try:
            for task in done:
                if task.exception():
                    raise task.exception()
        except ConnectionClosedError:
            console.print("[blue] Provider Connection was closed. Trying Reconnect")
        except:
            console.print_exception()
                    
        logger.error(f"Provider: Lost connection inbetween everything :( {[ task.exception() for task in done]}")
        logger.error(f'Provider: Reconnecting')

        

        if self.connection: await self.connection.close()

        for task in self.pending:
            task.cancel()

        console.log("Trying to Reconnect")
        self.current_retries = 0 # reset retries after one successfull connection
        await self.startup() # Attempt to ronnect again
        

    async def connect_websocket(self):
        try:
            uri = f"{self.websocket_protocol}://{self.websocket_host}:{self.websocket_port}/provider/?token={self.client.auth.access_token}"
            self.connection = await websockets.client.connect(uri)
        except:
            #TODO: Better TokenExpired Handling
            self.client.auth.refetch()
            uri = f"{self.websocket_protocol}://{self.websocket_host}:{self.websocket_port}/provider/?token={self.client.auth.access_token}"
            self.connection = await websockets.client.connect(uri)

        logger.info("Sueccess fully connected Provider ")


    async def consumer(self):
        async for message in self.connection:
            await self.incoming_queue.put(message)

    async def producer(self):
        while True:
            message = await self.outgoing_queue.get()
            await self.connection.send(message.to_channels())

            self.outgoing_queue.task_done()

    async def forward(self, message: MessageModel) -> str:
        logger.info(f"Sending {message}")
        await self.outgoing_queue.put(message)

    async def workers(self):
        while True:
            message_str = await self.incoming_queue.get()
            logger.info(f"Incoming Message {message_str}")
            try:
                message = expandToMessage(json.loads(message_str))
                logger.warn(f"Incoming Message {message}")
                await self.on_message(message)
            except:
                raise


            self.incoming_queue.task_done()
    




    

