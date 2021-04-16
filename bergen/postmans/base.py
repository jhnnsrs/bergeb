from abc import ABC, abstractmethod
from asyncio.futures import Future
from bergen.messages.postman.progress import ProgressLevel
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
    
    def __init__(self, requires_configuration=True, loop=None, client=None, **kwargs) -> None:
        super().__init__(**kwargs)
        assert loop is not None, "Please provide a Loop to your Postman, Did you forget to call super.init with **kwargs?"
        self.loop = loop or asyncio.get_event_loop()
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


        # Assign Function related
        if isinstance(message, AssignReturnMessage):
            future = self.assignments.pop(reference)
            if not future.cancelled():
                future.set_result(message)
            else:
                if reference in self.assignment_progress_functions:
                    function = self.assignment_progress_functions[reference]
                    function(f"[red]Race Condition! Assignation Return before being Cancelled on the Server. Omitting Result!", level=ProgressLevel.DEBUG)

        elif isinstance(message, AssignProgressMessage):
            function = self.assignment_progress_functions[reference]
            function(message.data.message, level=message.data.level)

        elif isinstance(message, AssignCriticalMessage):
            future = self.assignments.pop(reference)
            future.set_exception(NodeException(message.data.message))


        # Unassign Function related
        elif isinstance(message, UnassignDoneMessage):
            future = self.unassignments.pop(reference)
            future.set_result(message)

        elif isinstance(message, UnassignProgressMessage):
            function = self.unassignment_progress_functions[reference]
            function(message.data.message, level=message.data.level)

        elif isinstance(message, UnassignCriticalMessage):
            future = self.unassignments.pop(reference)
            future.set_exception(NodeException(message.data.message))


        # Reserve Function related
        elif isinstance(message, ReserveDoneMessage):
            future = self.reservations.pop(reference)
            future.set_result(message)

        elif isinstance(message, ReserveProgressMessage):
            function = self.reservations_progress_functions[reference]
            function(message.data.message, level=message.data.level)

        elif isinstance(message, ReserveCriticalMessage):
            future = self.reservations.pop(reference)
            future.set_exception(HostException(message.data.message))


        # Reserve Function related
        elif isinstance(message, UnreserveDoneMessage):
            future = self.unreservations.pop(reference)
            future.set_result(message)

        elif isinstance(message, UnreserveProgressMessage):
            function = self.unreservations_progress_functions[reference]
            function(message.data.message, level=message.data.level)

        elif isinstance(message, UnreserveCriticalMessage):
            future = self.unreservations.pop(reference)
            future.set_exception(HostException(message.data.message))


        elif isinstance(message, ExceptionMessage):
            if reference in self.assignments: self.assignments.pop(reference).set_exception(message.toException()) 
            if reference in self.unassignments: self.unassignments.pop(reference).set_exception(message.toException()) 
            if reference in self.reservations: self.reservations.pop(reference).set_exception(message.toException()) 
            if reference in self.unreservations: self.unreservations.pop(reference).set_exception(message.toException())

        else:

            raise Exception("Unknown message type", message )
        


    async def unassign(self, assignation: str, on_progress=None, bounced=None) -> UnassignDoneMessage:
        """ Takes a previously assigned reference to an assignation and cancel the assignation

        Args:
            assignation (str): The reference to the assignation
            on_progress ([type], optional): A callacble for the progress. Defaults to None.

        Raises:
            e: A cancellation Error

        Returns:
            None
        """
        unassign_reference = str(uuid.uuid4()) 

        future = self.loop.create_future()
        self.unassignments[unassign_reference] = future


        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            self.unassignment_progress_functions[unassign_reference] = on_progress
            with_progress = True

        unassign = build_unassign_messsage(unassign_reference,assignation, with_progress=with_progress, bounced=bounced)


        await self.forward(unassign)

        try:
            future.add_done_callback(lambda x: logger.info(x))
            return await future

        except asyncio.CancelledError as e:
            if on_progress: on_progress(f"[red]Cancelled Unassignment {unassign_reference}")
            raise e



    async def assign(self, reservation: str, shrinked_args, shrinked_kwargs = {}, on_progress: Callable = None, bounced = None) -> AssignReturnMessage:
        """Assign takes a reservation and the serialized arguments as well as kwargs and awaits the result call, it will return
        the Assignation Returns.

        Attention! This function should only be called within an ongoing reservation

        Args:
            reservation (str): The reference of the reservation you want to assign to
            serialized_args ([type]): The serialized Args
            serialized_kwargs (dict, optional): [description]. The serialized Kwargs Defaults to {}.
            on_progress (Callable, optional): A on_progress callable for Assign and Unassign Progress. Defaults to None.
            bounced (Dict, optional): A dict using the bounced context from another assignment (works only on backend applications with can_forward_bounce scope

        Raises:
            e: Cancellation Error

        Returns:
            List: The Unserialized Outputs of the Call
        """
        
        assign_reference = str(uuid.uuid4()) 

        future = self.loop.create_future()
        self.assignments[assign_reference] = future

        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            self.assignment_progress_functions[assign_reference] = on_progress
            with_progress = True
            
        assign = build_assign_message(assign_reference, reservation, shrinked_args, kwargs=shrinked_kwargs, with_progress=with_progress, bounced=bounced)
        await self.forward(assign)

        try:
            future.add_done_callback(lambda x: logger.info(x))
            return await future


        except asyncio.CancelledError as e:
            if on_progress: on_progress(f"[red]Cancelled Assignment {assign_reference}", level=ProgressLevel.DEBUG)
            try:
                unassign = await self.unassign(assign_reference, bounced=bounced)
            except:
                console.print_exception()
            raise e


    async def unreserve(self, reservation, on_progress: Callable = None, bounced=None) -> UnreserveDoneMessage:
        unreserve_reference = str(uuid.uuid4()) 

        future = self.loop.create_future()
        self.unreservations[unreserve_reference] = future


        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            self.unreservations_progress_functions[unreserve_reference] = on_progress
            with_progress = True

        unassign = build_unreserve_messsage(unreserve_reference, reservation, with_progress=with_progress, bounced=bounced)
        await self.forward(unassign)

        try:
            future.add_done_callback(lambda x: logger.info(x))
            return await future

        except asyncio.CancelledError as e:
            if on_progress: on_progress(f"[red]Cancelled Unreservation {unreserve_reference}", level=ProgressLevel.DEBUG)
            raise e



    async def reserve(self, node_id: str = None, template_id: str = None , params_dict: dict = {}, on_progress: Callable = None, bounced=None) -> ReserveDoneMessage:
        """[summary]

        Args:
            node_id (str, optional): [description]. Defaults to None.
            template_id (str, optional): [description]. Defaults to None.
            params_dict (dict, optional): [description]. Defaults to {}.
            on_progress (Callable, optional): [description]. Defaults to None.

        Raises:
            e: [description]

        Returns:
            str: The 
        """

        reserve_reference = str(uuid.uuid4()) 

        future = self.loop.create_future()
        self.reservations[reserve_reference] = future

        with_progress = False
        if on_progress:
            assert callable(on_progress), "on_progress if provided must be a function/lambda"
            self.reservations_progress_functions[reserve_reference] = on_progress
            with_progress = True
            
        reserve = build_reserve_message(reserve_reference, node_id, template_id, params_dict=params_dict, with_progress=with_progress,bounced=bounced)
        await self.forward(reserve)

        try:
            future.add_done_callback(lambda x: logger.info(x))
            reserve_done: ReserveDoneMessage = await future
            await reserve_done

        except asyncio.CancelledError as e:
            if on_progress: on_progress(f"[red]Cancelled Reservation {reserve_reference}")
            unassign = await self.unreserve(self, reserve_reference, bounced=bounced)
            raise e

    async def reserve_stream(self, node_id: str = None, template_id: str = None , params_dict: dict = {}, with_progress= True, bounced=None) -> MessageModel:
        reserve_reference = str(uuid.uuid4())
        self.reservation_stream_queues[reserve_reference] = asyncio.Queue()


        reserve = build_reserve_message(reserve_reference, node_id, template_id, params_dict=params_dict, with_progress=with_progress, bounced=bounced)
        await self.forward(reserve)

        try:
            while True:
                parsed_message = await self.reservation_stream_queues[reserve_reference].get()
                yield parsed_message

        except asyncio.CancelledError as e:
            # Otherwise we will still listen to the stream on cancellation
            del self.reservation_stream_queues[reserve_reference]
            unreserve = await self.unreserve(reserve_reference, bounced=bounced)
            raise e # Otherwise we


    async def assign_stream(self, reservation: str, serialized_args, serialized_kwargs = {}, with_progress = None, bounced=None) -> MessageModel:
        assign_reference = str(uuid.uuid4())
        self.assignment_stream_queues[assign_reference] = asyncio.Queue()

        assign = build_assign_message(assign_reference, reservation, serialized_args, kwargs=serialized_kwargs, with_progress=with_progress, bounced=bounced)
        await self.forward(assign)

        try:
            while True:
                parsed_message = await self.assignment_stream_queues[assign_reference].get()
                yield parsed_message
                
        except asyncio.CancelledError as e:
            # Otherwise we will still listen to the stream on cancellation
            del self.assignment_stream_queues[assign_reference]
            unassign = await self.unassign(self, assign_reference, bounced=bounced)
            # TODO: Maybe yield here as well?
            raise e # Otherwise we