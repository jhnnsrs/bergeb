

from abc import ABC, abstractmethod
from bergen.messages.postman.provide.bounced_cancel_provide import BouncedCancelProvideMessage
from bergen.messages.postman.provide.provide_progress import ProvideProgressMessage
from bergen.messages.postman.provide.bounced_provide import BouncedProvideMessage
from bergen.messages.utils import expandToMessage
from bergen.messages.base import MessageModel
from bergen.provider.base import BaseHelper, BaseProvider
import logging
import asyncio
import websockets
import json
import asyncio
try:
    from asyncio import create_task
except ImportError:
    #python 3.6 fix
    create_task = asyncio.ensure_future


logger = logging.getLogger()



DEBUG = True

class WebsocketProvider(BaseProvider):
    ''' Is a mixin for Our Bergen '''

    def __init__(self, host= None, port= None, protocol=None, auto_reconnect=True, auth=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.websocket_host = host
        self.websocket_port = port
        self.websocket_protocol = protocol
        self.token = auth["token"]

        self.pending = None

        self.auto_reconnect= auto_reconnect
        self.allowed_retries = 2
        self.current_retries = 0


    async def connect(self):
        self.incoming_queue = asyncio.Queue()
        self.outgoing_queue = asyncio.Queue()
        self.tasks = {}

        self.startup_task = create_task(self.startup())


    async def disconnect(self) -> str:
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

            logger.error(f"Peasent Connection failed {e}")
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

        if DEBUG: 
            for task in done:
                if task.exception():
                    raise task.exception()
                    
        logger.error(f"Provider: Lost connection inbetween everything :( {[ task.exception() for task in done]}")
        logger.error(f'Provider: Reconnecting')

        for task in self.pending:
            task.cancel()

        if self.connection: await self.connection.close()
        self.current_retries = 0 # reset retries after one successfull connection
        await self.startup() # Attempt to ronnect again
        

    async def connect_websocket(self):
        uri = f"{self.websocket_protocol}://{self.websocket_host}:{self.websocket_port}/provider/?token={self.token}"
        self.connection = await websockets.client.connect(uri)


    async def consumer(self):
        logger.warning(" [x] Awaiting Provision Calls")
        async for message in self.connection:
            logger.info(f"Incoming Provide {message}")
            await self.incoming_queue.put(message)


    async def producer(self):
        while True:
            message = await self.outgoing_queue.get()
            await self.connection.send(message.to_channels())


    async def send_to_connection(self, message: MessageModel):
        logger.info(f"Sending {message}")
        await self.outgoing_queue.put(message)
       

    async def workers(self):
        while True:
            message_str = await self.incoming_queue.get()
            message = expandToMessage(json.loads(message_str))

            if isinstance(message, BouncedProvideMessage):
                logger.info("Received Provide Request")
                assert message.data.template is not None, "Received Provision that had no Template???"

                pod, task = await self.provideTemplate(message.meta.reference, message.data.template)
                self.provisions[message.meta.reference] = task # Run in parallel

                progress = ProvideProgressMessage(data={
                    "level": "INFO",
                    "message": f"Pod Pending {pod.id}"
                }, meta={"extensions": message.meta.extensions, "reference": message.meta.reference})

                await self.send_to_connection(progress)



            elif isinstance(message, BouncedCancelProvideMessage):

                if message.data.reference in self.tasks: 
                    logger.info("Cancellation for Provision received. Canceling!")
                    provision = self.provisions[message.data.reference]
                    if not provision.done():
                        provision.cancel()
                        #TODO: await self.send_to_connection(progress)
                        logger.warn("Canceled Provision!!")

                    #TODO: await self.send_to_connection(progress) if task was already done
                else:
                    logger.error("Received Cancellation for task that was not in our tasks..")

            else: raise Exception("Received Unknown Task")
            self.incoming_queue.task_done()




    

