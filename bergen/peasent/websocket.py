

from abc import ABC, abstractmethod
from re import template
from bergen.messages.allowance import AllowanceMessage
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
        except:

            logger.error(f"Peasent Connection failed")
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

        worker_task = create_task(
            self.workers()
        )



        done, pending = await asyncio.wait(
            [consumer_task, worker_task],
            return_when=asyncio.FIRST_EXCEPTION
        )

        logger.error(f"Lost connection inbetween everything :( {[ task.exception() for task in done]}")
        logger.error(f'Reconnecting')

        for task in pending:
            task.cancel()

        self.current_retries = 0 # reset retries after one successfull connection
        await self.startup() # Attempt to ronnect again
        

    async def connect_websocket(self):

        hostable_pods = [str(podid) for podid, function in self.podid_pod_map.items()]
        hostable_pods_qstring = ",".join(hostable_pods)

        uri = f"{self.websocket_protocol}://{self.websocket_host}:{self.websocket_port}/peasent/{self.unique_name}/?token={self.token}&pods={hostable_pods_qstring}"
        
        self.connection = await websockets.client.connect(uri)
        # Our initial payload will be the Pods that were registered! Our allowance
        message = await self.connection.recv()
        allowance = AllowanceMessage.from_channels(message=message)

        self.pod_template_map = allowance.data.pod_template_map
        logger.info(f"We are able to host these pods {[ pod for pod, template in self.pod_template_map.items()]}")


    async def consumer(self):
        logger.warning(" [x] Awaiting Node Calls")
        async for message in self.connection:
            await self.incoming_queue.put(message)


    async def send_to_connection(self, message: AssignationMessage):
        await self.connection.send(message.to_channels())
       

    async def workers(self):
        while True:
            message = await self.incoming_queue.get()
            message = AssignationMessage.from_channels(message)
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
                assert message.data.pod is not None, "Received assignation that had no Pod?"
                #
                task = create_task(self.podid_function_map[message.data.pod](message))
                self.tasks[message.data.reference] = task # Run in parallel


            self.incoming_queue.task_done()


    

