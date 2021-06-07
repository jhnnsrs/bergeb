

import asyncio
from asyncio.tasks import Task
from bergen.messages.postman.log import LogLevel
from bergen.debugging import DebugLevel
from bergen.handlers.base import Connector
from bergen.messages import *
from bergen.handlers import *
from bergen.console import console
from bergen.utils import *
from bergen.legacy.utils import create_task


class Actor:
    expandInputs = True
    shrinkOutputs = True

    def __init__(self, connector: Connector, queue:asyncio.Queue = None, loop=None) -> None:
        self.queue = queue or asyncio.Queue()
        self.connector = connector
        self.loop = loop or asyncio.get_event_loop()
        self._provided = False

        self.assignments = {}
        self.assign_handler_map = {}
        self.unassign_handler_map = {}

        self.template = None
        pass

    async def log(self, message, level="INFO"):
        console.log(f"[red] Actor: {message}")


    async def on_provide(self, provide: ProvideHandler):
        await self.log(f"Providing {provide}")

    async def on_unprovide(self, provide: ProvideHandler):
        await self.log(f"Unproviding {provide}")


    async def _on_provide_message(self, message: BouncedProvideMessage):
        self.provide_handler = ProvideHandler(message, self.connector)
        try:
            await self.provide_handler.log("Providing ssss", level=LogLevel.INFO)
            self.template = await self.provide_handler.get_template()
            provision_context = await self.on_provide(self.provide_handler)

            if provision_context is not None:
                self.provide_handler.set_context(provision_context)

            await self.provide_handler.log("Provision Done", level=LogLevel.INFO)   
            self._provided = True
            await self.provide_handler.pass_done()

        except Exception as e:
            console.print_exception()
            await self.provide_handler.pass_exception(e)


            
    async def run(self, bounced_provide: BouncedProvideMessage):
        ''' An infinitie loop assigning to itself'''
        try:
            await self._on_provide_message(bounced_provide)

            try:
                assert self._provided, "We didnt provide this actor before running"
                
                while True:
                    message = await self.queue.get()

                    if isinstance(message, BouncedForwardedAssignMessage):
                        task = create_task(self.on_assign(message))
                        task.add_done_callback(self.check_if_assignation_cancelled)
                        self.assignments[message.meta.reference] = task

                    elif isinstance(message, BouncedUnassignMessage):
                        if message.data.assignation in self.assignments: 
                            await self.log(f"Cancellation of assignment {message.data.assignation}", level=DebugLevel.INFO)
                            task = self.assignments[message.data.assignation]
                            if not task.done():
                                task.cancel()
                                unassign_done = UnassignDoneMessage(data={
                                    "assignation": message.data.assignation
                                },
                                    meta = {
                                        "reference": message.meta.reference,
                                        "extensions": message.meta.extensions
                                    }
                                )
                                await self.connector.forward(unassign_done)
                                await self.log(f"Cancellation of assignment suceeded", level=DebugLevel.INFO)
                            else:
                                unassign_critical = UnassignCriticalMessage(data={
                                    "message": "Task was already done",
                                    "type": "Exception"
                                },
                                    meta = {
                                        "reference": message.meta.reference,
                                        "extensions": message.meta.extensions
                                    }
                                )
                                await self.connector.forward(unassign_critical)
                                await self.log(f"Cancellation of assignment failed. Task was already Done", level=DebugLevel.INFO)
                                #TODO: Maybe send this to arkitekt as well?
                        else:
                            unassign_done = UnassignDoneMessage(data={
                                    "assignation": message.data.assignation
                                },
                                    meta = {
                                        "reference": message.meta.reference,
                                        "extensions": message.meta.extensions
                                    }
                                )
                            await self.connector.forward(unassign_done)
                            await self.log(f"There was nether an assignment on this Worker... Sending Done", level=DebugLevel.INFO)
                    else:
                        raise Exception(f"Type not known {message}")

                    self.queue.task_done()
                
            except Exception as e:
                console.print_exception()

        except asyncio.CancelledError:
            await self.on_unprovide(self.provide_handler)
            await self.log("Actor was beeing cancelled")
            raise


    
    def check_if_assignation_cancelled(self, task: Task):
        if task.cancelled():
            console.log(f"[yellow] Assignation {task} Cancelled and is now Done")
        elif task.exception():
            console.log(f"[red] Assignation {task} Failed with {str(task.exception())}")
        elif task.done():
            console.log(f"[green] Assignation {task} Succeeded and is now Done")


    async def on_assign(self, assign: BouncedForwardedAssignMessage):
        assign_handler = AssignHandler(message=assign, connection=self.connector)
        self.assign_handler_map[assign.meta.reference] = assign_handler

        await assign_handler.log(f"Assignment received", level=DebugLevel.INFO)
        try:
            try:
                args, kwargs = await expandInputs(node=self.template.node, args=assign.data.args, kwargs=assign.data.kwargs) if self.expandInputs else (assign.data.args, assign.data.kwargs)
           
                await self._assign(assign_handler, args, kwargs) # We dont do all of the handling here, as we really want to have a generic class for Generators and Normal Functions
            
            except Exception as e:
                # As broad as possible to send further
                await assign_handler.log("Captured an Exception on the Broadest Level of Assignment. Please make sure to capure this exception before.", level=LogLevel.WARN)
                console.print_exception()
                await assign_handler.pass_exception(e)

        except asyncio.CancelledError as e:
            await assign_handler.log(f"Cancellation of Assignment suceeded", level=DebugLevel.INFO)
            await assign_handler.pass_cancelled()
            raise e
    
    async def __aenter__(self):
        await self.reserve()
        return self

    async def __aexit__(self, type, value, traceback):
        await self.unreserve()
