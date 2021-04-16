
from bergen.messages.base import MessageModel
from bergen.messages.utils import expandToMessage
import json
from bergen.entertainer.base import BaseEntertainer
import logging
import asyncio
import websockets
from bergen.console import console
import asyncio
try:
    from asyncio import create_task
except ImportError:
    #python 3.6 fix
    create_task = asyncio.ensure_future


logger = logging.getLogger()





class WebsocketEntertainer(BaseEntertainer):
    ''' Is a mixin for Our Bergen '''

    def __init__(self, host= None, port= None, protocol=None, auto_reconnect=True, auth: dict= None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.websocket_host = host
        self.websocket_port = port
        self.websocket_protocol = protocol
        self.token = auth["token"]
        
        self.auto_reconnect= auto_reconnect
        self.allowed_retries = 2
        self.current_retries = 0

    async def connect(self):
        self.incoming_queue = asyncio.Queue()
        self.outgoing_queue = asyncio.Queue()
        self.tasks = []

        self.startup_task = create_task(self.startup())

    async def disconnect(self) -> str:
        for reference, task in self.assignments.items():
            if not task.done():
                logger.info(f"Cancelling Assignment {task}")
                task.cancel()

        if self.connection: await self.connection.close()

        if self.pending:
            for task in self.pending:
                task.cancel()

        logger.info("Entertainer disconnected")

        
    async def startup(self):
        try:
            await self.connect_websocket()
        except Exception as e:

            logger.error(f"Entertainer Connection failed {e}")
            self.current_retries += 1
            if self.current_retries < self.allowed_retries and self.auto_reconnect:
                sleeping_time = (self.current_retries + 1)
                logger.info(f"Retrying in {sleeping_time} seconds")
                await asyncio.sleep(sleeping_time)
                await self.startup()
            else:
                logger.error("No reconnecting attempt envisioned. Shutting Down!")
                return

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

        logger.error(f"Lost connection inbetween everything :( {[ task.exception() for task in done]}")
        logger.error(f'Reconnecting')

        for task in self.pending:
            task.cancel()

        if self.connection: await self.connection.close()
        self.current_retries = 0 # reset retries after one successfull connection
        await self.startup() # Attempt to ronnect again
        

    async def connect_websocket(self):

        uri = f"{self.websocket_protocol}://{self.websocket_host}:{self.websocket_port}/host/?token={self.token}"
        
        self.connection = await websockets.client.connect(uri)
        logger.info("Connecting as Entertainer")


    async def consumer(self):
        logger.warning(" [x] Awaiting Entertaining Calls")
        async for message in self.connection:
            await self.incoming_queue.put(message)

    async def producer(self):
        while True:
            message = await self.outgoing_queue.get()
            await self.connection.send(message.to_channels())

            self.outgoing_queue.task_done()

    async def forward(self, message: MessageModel):
        await self.outgoing_queue.put(message)


    async def workers(self):
        while True:
            message_str = await self.incoming_queue.get()
            message = expandToMessage(json.loads(message_str))
            logger.info(f"Received Message {message}")
            await self.on_message(message)
            self.incoming_queue.task_done()


    


    
    

