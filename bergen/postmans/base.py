from abc import ABC, abstractmethod
from asyncio.futures import Future
from contextvars import Context
from bergen.messages.postman.log import LogLevel
from bergen.messages import *
from bergen.messages.base import MessageModel
from bergen.postmans.utils import build_assign_message, build_reserve_message, build_unassign_messsage, build_unreserve_messsage
import uuid
from bergen.hookable.base import Hookable
from bergen.schema import Node, Pod, Template
from typing import Callable, Dict, List
from aiostream import stream
import asyncio
import logging
from bergen.console import console

logger = logging.getLogger(__name__)

ReferenceQueueMap = Dict[str, asyncio.Queue]
ReferenceFutureMap = Dict[str, Future]
ReferenceProgressFuncMap = Dict[str, Callable]

class NodeException(Exception):
    pass

class HostException(Exception):
    pass

class ProtocolException(Exception):
    pass

class BasePostman(Hookable):
    """ A Postman takes node requests and translates them to Bergen calls, basic implementations are GRAPHQL and PIKA"""
    
    def __init__(self, client, requires_configuration=True, loop=None,**kwargs) -> None:
        super().__init__(**kwargs)
        self.loop = loop or client.loop
        self.client = client

        # Assignments and their Cancellations
        self.assignment_stream_queues: ReferenceQueueMap = {}
        self.assignments: ReferenceFutureMap = {}
        self.assignment_progress_functions: ReferenceProgressFuncMap = {}

        self.unassignments: ReferenceFutureMap = {}
        self.unassignment_progress_functions: ReferenceProgressFuncMap = {}

        # Reservations and their Cancellations
        self.reservation_stream_queues: ReferenceQueueMap = {}
        self.reservations: ReferenceFutureMap = {}
        self.reservations_progress_functions: ReferenceProgressFuncMap = {}

        self.unreservations: ReferenceFutureMap = {}
        self.unreservations_progress_functions: ReferenceProgressFuncMap = {}


    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def forward(self, message: MessageModel):
        return NotImplementedError("This is abstract")


    async def on_message(self, message: MessageModel):
        # First we check the streams
        reference = message.meta.reference

        if reference in self.assignment_stream_queues:
            return await self.assignment_stream_queues[reference].put(message)

        if reference in self.reservation_stream_queues:
            return await self.reservation_stream_queues[reference].put(message)

        else:
            console.log(f"Unknown message {message}") 
        

    async def stream_reserve_to_queue(self, queue, node_id: str = None, template_id: str = None , provision: str = None, params_dict: dict = {}, with_log= True, context=None):
        reserve_reference = str(uuid.uuid4())
        self.reservation_stream_queues[reserve_reference] = queue
        reserve = build_reserve_message(reserve_reference, node_id, template_id, provision, params_dict=params_dict, with_log=with_log, context=context)
        await self.forward(reserve)
        return reserve_reference

    async def send_unreserve(self, reservation: str = None, context: Context=None):
        unreserve_reference = str(uuid.uuid4())
        unreserve = build_unreserve_messsage(unreserve_reference, reservation, context=context)
        await self.forward(unreserve)
        return unreserve_reference

    async def delete_reservequeue(self, reference: str = None):
        del self.reservation_stream_queues[reference]

    async def stream_assign_to_queue(self, queue, reservation: str, shrinked_args, shrinked_kwargs = {}, with_log=True, persist=True, context = None):
        assign_reference = str(uuid.uuid4())
        self.assignment_stream_queues[assign_reference] = queue
        assign = build_assign_message(assign_reference, reservation, shrinked_args, kwargs=shrinked_kwargs, with_log=with_log, context=context, persist=persist)
        await self.forward(assign)
        return assign_reference

    async def send_unassign(self, assignation: str = None, context: Context= None):
        unassign_reference = str(uuid.uuid4())
        unreserve = build_unassign_messsage(unassign_reference, assignation, context=context)
        await self.forward(unreserve)
        return unassign_reference

    async def delete_assignqueue(self, reference: str = None):
        del self.assignment_stream_queues[reference]

    