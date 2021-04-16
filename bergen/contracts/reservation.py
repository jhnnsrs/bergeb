from asyncio.futures import Future
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


logger = logging.getLogger(__name__)





class Reservation:

    def __init__(self, node: Node, loop=None, monitor: Monitor = None, ignore_node_exceptions=False, bounced=None, **params) -> None:
        bergen = get_current_client()
        self._postman = bergen.getPostman()

        self.node = node
        self.params = ReserveParams(**params)
        self.monitor = monitor or current_monitor.get()
        self.ignore_node_exceptions = ignore_node_exceptions

        self.bounced = bounced # with_bounced allows us forward bounced checks
        if self.bounced:
            assert "can_forward_bounce" in bergen.auth.scopes, "In order to use with_bounced forwarding you need to have the can_forward_bounced scope"

        if self.monitor:
            self.monitor.addRow(self.build_panel())
            self.log = lambda level, message: self.table.add_row(level, message)
            self.on_progress = lambda message, level: self.log(f"[magenta]{level}", message) if self.monitor.progress else None
        else:
            self.log = lambda level, message: logger.info(message)
            self.on_progress = False


        self.loop = loop or asyncio.get_event_loop()
        # Status
        self.running = False
        self.reservation = None
        self.critical_error = None
        self.recovering = False #TODO: Implement

        pass
    
    def build_panel(self):
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

    async def assign(self, *args, **kwargs):
        assert self.node.type == NodeType.FUNCTION, "You cannot assign to a Generator Node, use the stream Method!"
        if self.critical_error is not None:
            
            self.log("[red]ASSIGN",f"Contract is broken and we can not assign. Exiting!")
        try:
            shrinked_args, shrinked_kwargs = await shrinkInputs(self.node, args, kwargs)
            return_message = await self._postman.assign(self.reservation, shrinked_args, shrinked_kwargs=shrinked_kwargs, on_progress=self.on_progress, bounced=self.bounced)
            return await expandOutputs(self.node, return_message.data.returns)

        except AssignmentException as e:
            self.log("[red]ASSIGN", str(e))
            if not self.ignore_node_exceptions: raise e
        except Exception as e:
            raise e



    async def stream(self, *args, **kwargs):
        assert self.node.type == NodeType.GENERATOR, "You cannot stream a Function Node, use the assign Method!"
        if self.critical_error is not None:
            self.log("[red]ASSIGN",f"Contract is broken and we can not assign. Exiting!")
        try:
            shrinked_args, shrinked_kwargs = await shrinkInputs(self.node, args, kwargs)
            async for message in self._postman.assign_stream(self.reservation, shrinked_args, serialized_kwargs=shrinked_kwargs, with_progress=True, bounced=self.bounced):

                if isinstance(message, AssignYieldsMessage):
                    yield await expandOutputs(self.node, message.data.returns)

                if isinstance(message, AssignProgressMessage):
                    self.on_progress(message.data.message, message.data.level)
                
                if isinstance(message, AssignCriticalMessage):
                    raise AssignmentException(message.data.type + message.data.message)

                if isinstance(message, AssignDoneMessage):
                    self.log("ASSIGN", f'Done')
                    break

        except asyncio.CancelledError as e:
            self.log("[red] Cancelled")
            raise e

        except AssignmentException as e:
            self.log("[red]ASSIGN", str(e))
            if not self.ignore_node_exceptions: raise e

        
    

    async def contract_worker(self):
        self.running = True
        try:
            async for message in self._postman.reserve_stream(node_id=self.node.id, params_dict=self.params.dict(), with_progress=True, bounced=self.bounced):
                # Before here because Reserve Critical is actually an ExceptionMessage
                #TODO: Undo this

                if isinstance(message, ReserveProgressMessage):
                    self.log(f'[green]{message.data.level.value}', message.data.message)

                if isinstance(message, ProvideProgressMessage):
                    self.log(f'[magenta]{message.data.level.value}', message.data.message)

                if isinstance(message, ReserveCriticalMessage):
                    # Reserve Errors are Errors that happen during the Reservation
                    self.log(f'[red]EXCEPTION', message.data.message)
                    self.critical_error = message

                if isinstance(message, ProvideCriticalMessage):
                    # Reserve Errors are Errors that happen during the Reservation
                    self.log(f'[red]EXCEPTION', message.data.message)
                    self.critical_error = message

                elif isinstance(message, ExceptionMessage):
                    # Porotocol Exceptions are happening on the start
                    self.contract_started.set_exception(message.toException())
                    return

                elif isinstance(message, ReserveDoneMessage):
                    # Once we acquire a reserved resource our contract (the inner part of the context can start)
                    self.contract_started.set_result(message.meta.reference)
        
        except asyncio.CancelledError as e:
            self.log("[green]DONE", "Unreserved Sucessfully")

 
    def cancel_reservation(self, future: Future):
        if future.exception():
            self.log("[red]Exception", str(future.exception()))
            raise future.exception()
        elif future.done():
            return


    async def start(self):
        return await self.__aenter__()

    async def end(self):
        await self.__aexit__()

    async def __aenter__(self):
        self.contract_started = self.loop.create_future()
        self.worker_task = self.loop.create_task(self.contract_worker())

        self.worker_task.add_done_callback(self.cancel_reservation)
        self.reservation = await self.contract_started
        self.log(f"[green]STARTED",f"Established Reservation {self.reservation}")
        return self

    async def __aexit__(self, *args, **kwargs):
        if not self.worker_task.done():
            #await self._postman.unreserve(reservation=self.reservation, on_progress=self.on_progress)
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                self.log("[green]EXIT", "Gently Exiting Reservation")
            except Exception as e:
                self.log(f"[red]CRITICAL", f"Exitigin with {str(e)}")



       