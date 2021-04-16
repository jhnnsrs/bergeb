

import asyncio
from asyncio.tasks import Task
from bergen.debugging import DebugLevel
from bergen.handlers.base import Connector
from bergen.messages import *
from bergen.handlers import *
from bergen.console import console
from bergen.utils import *


class Actor:

    def __init__(self, connector: Connector, queue:asyncio.Queue = None, loop=None) -> None:
        self.queue = queue or asyncio.Queue()
        self.connector = connector
        self.loop = loop
        self._provided = False

        self.assignments = {}
        self.reservations = {} # maps the reservations with its provided context

        self.reserve_handler_map = {}
        self.unreserve_handler_map = {}

        self.assign_handler_map = {}

        self.template = None
        pass



    async def on_provide(self, provide: ProvideHandler):
        pass

    async def on_unprovide(self, message):
        pass


    async def on_reserve(self, handler: ReserveHandler) -> Any:
        return None

    async def on_unreserve(self, unreserve_handler: UnreserveHandler, reserve_handler: ReserveHandler) -> None:
        return None

    
    async def _on_provide_message(self, bounced_provide: BouncedProvideMessage):
        self.provide_handler = ProvideHandler(bounced_provide, self.connector)
        try:
            self._current_provision_context = await self.on_provide(self.provide_handler)
            self.template = await self.provide_handler.get_template()
            self._provided = True
        except Exception as e:
            await self.provide_handler.pass_exception(e)


    async def _on_reserve_message(self, message: BouncedForwardedReserveMessage):
        reserve_handler = ReserveHandler(message, self.connector)
        self.reserve_handler_map[message.meta.reference] = reserve_handler

        try:
            await reserve_handler.log("Reserving", level=DebugLevel.INFO)

            reservation_context = await self.on_reserve(reserve_handler)
            if reservation_context is not None:
                reserve_handler.set_context(reservation_context)

            await reserve_handler.log("Reserving Done", level=DebugLevel.INFO)
            await reserve_handler.pass_done()

        except Exception as e:
            await reserve_handler.pass_exception(e)

    async def _on_unreserve_message(self, message: BouncedUnreserveMessage):
        unreserve_handler = UnreserveHandler(message, self.connector)
        self.unreserve_handler_map[message.meta.reference] = unreserve_handler

        try:
            await unreserve_handler.log("Unreserving", level=DebugLevel.INFO)
            info = await self.on_unreserve(unreserve_handler, self.reserve_handler_map[message.data.reservation])
            del self.reserve_handler_map[message.data.reservation]
            await unreserve_handler.pass_done()
        except Exception as e:
            await unreserve_handler.pass_exception(e)

            
    async def run(self, bounced_provide: BouncedProvideMessage):
        ''' An infinitie loop assigning to itself'''
        try:

            await self._on_provide_message(bounced_provide)

            try:
                assert self._provided, "We didnt provide this actor before running"
                
                while True:
                    message = await self.queue.get()

                    if isinstance(message, BouncedForwardedReserveMessage):
                        await self._on_reserve_message(message)

                    elif isinstance(message, BouncedUnreserveMessage):
                        await self._on_unreserve_message(message)

                    elif isinstance(message, BouncedForwardedAssignMessage):
                        task = asyncio.create_task(self.on_assign(message))
                        task.add_done_callback(self.check_if_assignation_cancelled)
                        self.assignments[message.meta.reference] = task

                    elif isinstance(message, BouncedUnassignMessage):
                        if message.data.assignation in self.assignments: 
                            await self.actor_progress(f"Cancellation of assignment {message.data.assignation}", level=DebugLevel.INFO)
                            task = self.assignments[message.data.assignation]
                            if not task.done():
                                task.cancel()
                                await self.helper.pass_cancelled_done(message)

                                await self.actor_progress(f"Cancellation of assignment suceeded", level=DebugLevel.INFO)
                            else:
                                await self.helper.pass_cancelled_failed(message, "Task was already Done")
                                await self.actor_progress(f"Cancellation of assignment failed. Task was already Done", level=DebugLevel.INFO)
                                #TODO: Maybe send this to arkitekt as well?
                        else:
                            raise Exception("Assignment never was at this pod. something went wrong")

                    else:
                        raise Exception(f"Type not known {message}")

                    self.queue.task_done()


            except asyncio.CancelledError:
                await self.on_unprovide(None)
                raise

        except Exception as e:
            console.print_exception()

    
    def check_if_assignation_cancelled(self, task: Task):
        if task.cancelled():
            console.log(f"[yellow] Assignation {task.get_name()} Cancelled and is now Done")
        elif task.exception():
            console.log(f"[red] Assignation {task.get_name()} Failed with {str(task.exception())}")
        elif task.done():
            console.log(f"[green] Assignation {task.get_name()} Succeeded and is now Done")


    async def on_assign(self, assign: BouncedForwardedAssignMessage):
        assign_handler = AssignHandler(message=assign, connection=self.connector)
        self.assign_handler_map[assign.meta.reference] = assign_handler
        reserve_handler = self.reserve_handler_map[assign.data.reservation]

        await assign_handler.log(f"Assignment received", level=DebugLevel.INFO)
        try:
            args, kwargs = await expandInputs(node=self.template.node, args=assign.data.args, kwargs=assign.data.kwargs)
            try:
                await self._assign(assign_handler, reserve_handler, args, kwargs) # We dont do all of the handling here, as we really want to have a generic class for Generators and Normal Functions
            
            except Exception as e:
                # As broad as possible to send further
                await assign_handler.pass_exception(e)
                # Pass this further up
                raise

        except asyncio.CancelledError as e:
            await reserve_handler.log(f"Cancellation of Assignment suceeded", level=DebugLevel.INFO)
            raise e
    
    async def __aenter__(self):
        await self.reserve()
        return self

    async def __aexit__(self):
        await self.unreserve()
