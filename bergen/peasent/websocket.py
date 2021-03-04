

from abc import ABC, abstractmethod
from bergen.messages.base import MessageModel
from re import template
from bergen.messages.activatepod import ActivatePodMessage
from typing import Union
from bergen.utils import ExpansionError, expandInputs
from bergen.messages.assignation import AssignationMessage
from bergen.schema import AssignationStatus, Template
from bergen.constants import OFFER_GQL, SERVE_GQL
from bergen.peasent.base import BaseHelper, BasePeasent
import logging
import namegenerator
import asyncio
import websockets
from bergen.models import Node
import inspect
import sys

import asyncio
try:
    from asyncio import create_task
except ImportError:
    #python 3.6 fix
    create_task = asyncio.ensure_future


logger = logging.getLogger()


class WebsocketHelper(BaseHelper):

    async def pass_yield(self, message, value):
        message.data.outputs = value
        message.data.status = AssignationStatus.YIELD
        await self.peasent.send_to_connection(message)

    async def pass_progress(self, message, value, percentage=None):
        message.data.status = AssignationStatus.PROGRESS#
        message.data.statusmessage = f'{percentage if percentage else "--"} : {value}'
        await self.peasent.send_to_connection(message)
        pass

    async def pass_result(self,message, value):
        message.data.outputs = value
        message.data.status = AssignationStatus.DONE
        await self.peasent.send_to_connection(message)

    async def pass_exception(self,message, exception):
        message.data.status = AssignationStatus.ERROR#
        message.data.statusmessage = str(exception)
        await self.peasent.send_to_connection(message)
        pass

class WebsocketPeasent(BasePeasent):
    helperClass = WebsocketHelper
    ''' Is a mixin for Our Bergen '''

    def __init__(self, *args, host= None, port= None, ssl = False, auto_reconnect=True, **kwargs) -> None:
        self.websocket_host = host
        self.websocket_port = port
        self.websocket_protocol = "wss" if ssl else "ws"


        self.auto_reconnect= auto_reconnect
        self.allowed_retries = 2
        self.current_retries = 0
        self.pod_template_map = {}

        super().__init__(*args,host=host, port=port, ssl=ssl,**kwargs)

    async def configure(self):
        self.incoming_queue = asyncio.Queue()
        self.outgoing_queue = asyncio.Queue()
        self.tasks = {}
        await self.startup()
        
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

        consumer_task = create_task(
            self.consumer()
        )

        producer_task = create_task(
            self.producer()
        )

        worker_task = create_task(
            self.workers()
        )

        done, pending = await asyncio.wait(
            [consumer_task, worker_task, producer_task],
            return_when=asyncio.FIRST_EXCEPTION
        )

        logger.error(f"Lost connection inbetween everything :( {[ task.exception() for task in done]}")
        logger.error(f'Reconnecting')

        for task in pending:
            task.cancel()

        self.current_retries = 0 # reset retries after one successfull connection
        await self.startup() # Attempt to ronnect again
        

    async def connect_websocket(self):

        uri = f"{self.websocket_protocol}://{self.websocket_host}:{self.websocket_port}/provider/?token={self.token}"
        
        self.connection = await websockets.client.connect(uri)

        for pod_id, function in self.podid_function_map.items():
            activate_pod = ActivatePodMessage(data={"pod": pod_id})
            logger.info(f"Requesting to Host {activate_pod}")
            await self.send_to_connection(activate_pod)



    async def consumer(self):
        logger.warning(" [x] Awaiting Node Calls")
        async for message in self.connection:
            logger.info(f"Incoming {message}")
            await self.incoming_queue.put(message)


    async def producer(self):
        while True:
            message = await self.outgoing_queue.get()
            await self.connection.send(message.to_channels())


    async def send_to_connection(self, message: MessageModel):
        await self.outgoing_queue.put(message)
       

    async def workers(self):
        while True:
            message = await self.incoming_queue.get()
            message = AssignationMessage.from_channels(message)
            logger.info("Received Assignation")
            if message.data.status == "CANCEL":
                if message.data.reference in self.tasks: 
                    logger.info("Cancellation for task received. Canceling!")
                    task = self.tasks[message.data.reference]
                    if not task.done():
                        task.cancel()
                        logger.warn("Canceled Task!!")
                else:
                    logger.error("Received Cancellation for task that was not in our tasks..")

            else:  
                assert message.data.template is not None, "Received assignation that had no Template???"
                task = create_task(self.templateid_function_map[message.data.pod](message))
                self.tasks[message.data.reference] = task # Run in parallel


            self.incoming_queue.task_done()


    

