from asyncio.futures import Future
from bergen.messages.postman.log import LogLevel
from contextvars import Context
from bergen.messages.postman.reserve.reserve_transition import ReserveState
from bergen import messages
from bergen.contracts.exceptions import AssignmentException
from bergen.registries.client import get_current_client
from bergen.schema import Node, NodeType
from bergen.monitor import Monitor, current_monitor
from bergen.messages.postman.reserve.params import ReserveParams
from bergen.messages import *
from bergen.utils import *
from rich.table import Table
from rich.panel import Panel
import asyncio
import logging
from bergen.console import console

logger = logging.getLogger(__name__)

class UnknownMessageError(Exception):
    pass


class ReservationError(Exception):
    pass


class CouldNotReserveError(ReservationError):
    pass


class IncorrectStateForAssignation(ReservationError):
    pass




class Reservation:

    def __init__(self, node: Node,
        reference: str = None,
        provision: str = None, 
        monitor: Monitor = None,
        ignore_node_exceptions=False,
        transition_hook=None,
        with_log=False,
        enter_on=[ReserveState.ACTIVE], 
        exit_on=[ReserveState.ERROR, ReserveState.CANCELLED],
        context: Context =None,
        loop=None,
         **params) -> None:


        # Reference
        self.monitor = monitor or current_monitor.get()
        self.client = get_current_client()
        self.loop = loop or self.client.loop
        self._postman = self.client.postman


        # Reservation Params
        self.reference = reference or str(uuid.uuid4())
        self.provision = provision
        self.node = node
        self.params = ReserveParams(**params)
        self.with_log = with_log or (self.monitor.log if self.monitor else None)
        self.context = context # with_bounced allows us forward bounced checks


        if self.context:
            assert "can_forward_bounce" in self.client.auth.scopes, "In order to use with_bounced forwarding you need to have the can_forward_bounced scope"

        # Exception Mangement
        self.ignore_node_exceptions = ignore_node_exceptions
        self.critical_error = None

        # State management
        self.transition_hook = transition_hook
        self.exit_states = exit_on
        self.enter_states = enter_on
        self.current_state = None


        if self.monitor:
            self.monitor.addRow(self.build_panel())
            self._log = lambda message, level: self.table.add_row(level, message)
        else:
            self._log = lambda message, level, : console.log(f"Reservation {self.reference} {level}: {message}")

        pass
    
    def log(self, message: str, level: LogLevel=LogLevel.DEBUG):
        """Logs a Message

        The Logged Message will be display on the Monitor if running inside a Monitor
        and send to the logging output.

        Args:
            message (str): The Message
            level (LogLevel, optional): The LogLevel. Defaults to LogLevel.DEBUG.
        """
        self._log(message, level)



    def build_panel(self) -> Panel:
        """Builds and returns a panel for a Monitor of this Reservation

        Returns:
            Panel: The Build Panel
        """
        heading_information = Table.grid(expand=True)
        heading_information.add_column()
        heading_information.add_column(style="green")

        reserving_table = Table(title=f"[bold green]Reserving on ...", show_header=False)

        for key, value in self.params.dict().items():
            reserving_table.add_row(key, str(value))

        heading_information.add_row(self.node.__rich__(), reserving_table)

        self.table = Table()
        self.table.add_column("Level")
        self.table.add_column("Message")

        columns = Table.grid(expand=True)
        columns.add_column()

        columns.add_row(heading_information)
        columns.add_row(self.table)

        return Panel(columns, title="Reservation")


    async def assign_async(self, *args, bypass_shrink=False, bypass_expand=False, persist=True, with_log=True, context=None, **kwargs):
        assert self.node.type == NodeType.FUNCTION, "You cannot assign to a Generator Node, use the stream Method!"

        if self.current_state in self.exit_states:
            raise IncorrectStateForAssignation(f"Current State {self.current_state} is an Element of Exit States {self.exit_states}")

        self.log(f"Streaming!", level=LogLevel.INFO)
        message_queue = asyncio.Queue()

        shrinked_args, shrinked_kwargs = await shrinkInputs(self.node, args, kwargs) if not bypass_shrink else (args, kwargs)
        assign_reference = await self._postman.stream_assign_to_queue(message_queue, self.reference, shrinked_args=shrinked_args, shrinked_kwargs=shrinked_kwargs, with_log=with_log, context=context or self.context)

        try:
            while True:
                message = await message_queue.get()

                if isinstance(message, AssignReturnMessage):
                    outs = await expandOutputs(self.node, message.data.returns) if not bypass_expand else message.data.returns    
                    return outs

                elif isinstance(message, AssignCancelledMessage):
                    raise AssignmentException(f"Assignment was cancelled from a different Agent: ID: {message.data.canceller}")

                elif isinstance(message, AssignLogMessage):
                    self.log(message.data.message, message.data.level)

                elif isinstance(message, AssignCriticalMessage):
                    raise AssignmentException(message.data.message)

                elif isinstance(message, AssignYieldsMessage):
                    raise AssignmentException("Received a Yield from a Node that should never yield! CRITICAL PROTOCOL EXCEPTION")

                else:
                    raise UnknownMessageError(message)


        except asyncio.CancelledError as e:
            self.log("Assigment Required Cancellation", level=LogLevel.INFO)

            unassign_reference = await self._postman.send_unassign(assign_reference, context=context)

            while True:
                message = await message_queue.get()
                if isinstance(message, AssignCancelledMessage):

                    if message.data.canceller != unassign_reference:
                        self.log("Canceller does not match our Cancellation Request, Race Condition?")
                    raise e

                else:
                    print("Raced Condition",message)



    async def stream(self, *args, bypass_shrink=False, bypass_expand=False, persist=True, context=None, with_log=True, **kwargs):
        assert self.node.type == NodeType.GENERATOR, "You cannot stream a Function Node, use the assign Method!"

        if self.current_state in self.exit_states:
            raise IncorrectStateForAssignation(f"Current State {self.current_state} is an Element of Exit States {self.exit_states}")

        self.log(f"Assigning!", level=LogLevel.INFO)
        message_queue = asyncio.Queue()

        shrinked_args, shrinked_kwargs = await shrinkInputs(self.node, args, kwargs) if not bypass_shrink else (args, kwargs)
        assign_reference = await self._postman.stream_assign_to_queue(message_queue, self.reference, shrinked_args=shrinked_args, shrinked_kwargs=shrinked_kwargs, with_log=with_log, context=context or self.context)

        try:
            while True:
                message = await message_queue.get()

                if isinstance(message, AssignYieldsMessage):
                    outs = await expandOutputs(self.node, message.data.returns) if not bypass_expand else message.data.returns    
                    yield outs

                elif isinstance(message, AssignDoneMessage):   
                    break

                elif isinstance(message, AssignCancelledMessage):
                    raise AssignmentException(f"Assignment was cancelled from a different Agent: ID: {message.data.canceller}")

                elif isinstance(message, AssignLogMessage):
                    self.log(message.data.message, message.data.level)

                elif isinstance(message, AssignCriticalMessage):
                    raise AssignmentException(message.data.message)

                elif isinstance(message, AssignReturnMessage):
                    raise AssignmentException("Received a Return from a Node that should never return! CRITICAL PROTOCOL EXCEPTION")

                else:
                    raise UnknownMessageError(message)


        except asyncio.CancelledError as e:
            self.log("Assigment Required Cancellation", level=LogLevel.INFO)

            unassign_reference = await self._postman.send_unassign(assign_reference, context=context)

            while True:
                message = await message_queue.get()

                if isinstance(message, AssignCancelledMessage):

                    if message.data.canceller != unassign_reference:
                        self.log("Canceller does not match our Cancellation Request, Race Condition?")
                    raise e

                elif isinstance(message, AssignLogMessage):
                    self.log(message.data.message, message.data.level)

                else:
                    print("Raced Condition",message)



    async def stream_worker(self, queue: asyncio.Queue):
        try:
            self.reference = await self._postman.stream_reserve_to_queue(queue, node_id=self.node.id, provision=self.provision, params_dict=self.params.dict(), with_log=self.with_log, context=self.context)
            print(self.reference)
            while True: 
                message = await queue.get()

                if isinstance(message, ReserveCriticalMessage):
                    if self.enter_future.done():
                        self.log(f"We have transitioned to a critical State {message.data.message}")
                        self.current_state = ReserveState.CRITICAL
                    else:
                        self.enter_future.set_exception(Exception(message.data.message))



                elif isinstance(message, ReserveTransitionMessage):
                        # Once we acquire a reserved resource our contract (the inner part of the context can start)
                        self.current_state  = message.data.state
                        if self.transition_hook: await self.transition_hook(self, message.data.state)
                        
                        if self.current_state in self.exit_states:
                            if not self.is_closing: self.log(f"Received Exitstate: {message.data.state}. Closing reservation at next assignment", level=LogLevel.CRITICAL)
                            return # This means we do no longer need to here about stuff

                        if self.current_state in self.enter_states:
                            if self.enter_future.done():
                                self.log("We are already entered.")
                            else:
                                self.enter_future.set_result(message.meta.reference)

                else:
                    console.log(message)

                queue.task_done()
        
        except Exception as e: 
            console.print_exception()
            if not self.enter_future.done():
                self.enter_future.set_exception(e)
            raise e


    async def cancel(self):
        await self._postman.send_unreserve(self.reference, context=self.context)

    async def start(self):
        return await self.__aenter__()

    async def end(self):
        await self.__aexit__()

    async def __aenter__(self):
        self.reservation_queue = asyncio.Queue()
        self.is_closing = False
        
        self.enter_future = self.loop.create_future()
        self.stream_task = self.loop.create_task(self.stream_worker(self.reservation_queue))

        print("Reached Here")

        try:
            self.enter_state = await self.enter_future
            return self

        except Exception as e:
            raise CouldNotReserveError(f"Could not Reserve Reservation {self.reference} for Node {self.node}") from e


    async def __aexit__(self, type, value, traceback):
        self.is_closing = True
        await self.cancel()

        if not self.stream_task.done():
            #TODO: Maybe make a Connection this
            self.is_closing = True
            await self.stream_task
            self.log("Reservation sucessfully unreserved", level=LogLevel.INFO)
        
        if value is not None and isinstance(value, asyncio.CancelledError): 
            print("Raising cancellation")
            raise value # passing our cancellation error


        

    
    def assign(self, *args, bypass_shrink=False, bypass_expand=False, persist=True, **kwargs):
        if False:
            return self.loop.run_until_complete(self.assign_async(*args, bypass_shrink=bypass_shrink, bypass_expand=bypass_expand, persist=persist, **kwargs))
        else:
            return self.assign_async(*args, bypass_shrink=bypass_shrink, bypass_expand=bypass_expand, persist=persist, **kwargs)

    def __enter__(self):
        self.in_sync = True
        future = self.loop.run_until_complete(self.__aenter__())
        return future

    def __exit__(self, *args, **kwargs):
        return  self.loop.run_until_complete(self.__aexit__(*args, **kwargs))



    




       