from abc import abstractmethod
from bergen.messages.postman.log import LogLevel
from bergen.clients.base import BaseBergen
from bergen.messages.base import MessageModel
from bergen.hookable.base import Hookable, hookable
from bergen.actors.base import Actor
from bergen.actors.functional import *
from bergen.provider.utils import createNodeFromActor, createNodeFromFunction
from bergen.console import console
from pydantic.main import BaseModel
from bergen.constants import OFFER_GQL
import logging
import asyncio
from bergen.models import Node, Template
import inspect
from bergen.messages import *

logger = logging.getLogger()


class PodPolicy(BaseModel):
    type: str



class OneExlusivePodPolicy(PodPolicy):
    type: str = "one-exclusive"

class MultiplePodPolicy(PodPolicy):
    type: str = "multiple"



def isactor(type):
    try:
        if issubclass(type, Actor):
            return True
        else:
            return False
    except Exception as e:
        return False



class BaseProvider(Hookable):
    ''' Is a mixin for Our Bergen '''
    helperClass = None


    def __init__(self, client: BaseBergen, loop=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.loop = loop or client.loop

        self.template_actorClass_map = {}

        self.message_queue = asyncio.Queue()
        self.provisions = {}
        
        
    def log(self, message):
        console.log(f"[blue] {message}")


    def template(self, node: Node, policy: PodPolicy = MultiplePodPolicy(), auto_provide=False, on_provide=None,  on_unprovide=None, bypass_shrink=False, bypass_expand=False, **implementation_details):
        console.print("[blue] Registered to Provide")
        console.print(node)

        def real_decorator(function_or_actor):
            assert callable(function_or_actor) or issubclass(function_or_actor, Actor), "Please only decorate functions or subclasses of Actor"
            # TODO: Check if function has same parameters as node

            template = Template.objects.update_or_create(**{
                "node": node.id,
                "params": implementation_details,
                "policy": policy.dict()
            })


            if isactor(function_or_actor):
                actorClass = function_or_actor
            else:
                is_coroutine = inspect.iscoroutinefunction(function_or_actor)
                is_asyncgen = inspect.isasyncgenfunction(function_or_actor)

                is_generatorfunction = inspect.isgeneratorfunction(function_or_actor)
                is_function = inspect.isfunction(function_or_actor)

                class_attributes = {"assign": staticmethod(function_or_actor), "expandInputs": not bypass_expand, "shrinkOutputs":  not bypass_shrink}


                if is_coroutine:
                    actorClass =  type(f"GeneratedActor{template.id}",(FunctionalFuncActor,), class_attributes)
                elif is_asyncgen:
                    actorClass =  type(f"GeneratedActor{template.id}",(FunctionalGenActor,), class_attributes)
                elif is_generatorfunction:
                    actorClass = type(f"GeneratedActor{template.id}", (FunctionalThreadedGenActor,),class_attributes)

                
                elif is_function:
                    actorClass = type(f"GeneratedActor{template.id}",(FunctionalThreadedFuncActor,), class_attributes)
                else:
                    raise Exception(f"Unknown type of function {function_or_actor}")
            

            self.register_actor(str(template.id), actorClass)

            return actorClass

        return real_decorator


    def enable(self, allow_empty_doc=False, widgets={}, **implementation_details):
        """Enables the decorating function as a node on the Arnheim, you will find it as
        @provider/

        Args:
            allow_empty_doc (bool, optional): Allow the enabled function to not have a documentation. Will automatically downlevel the Node Defaults to False.
            widgets (dict, optional): Enable special widgets for the parameters. Defaults to {}.
        """
        def real_decorator(function_or_actor):
            assert callable(function_or_actor) or issubclass(function_or_actor, Actor), "Please only decorate functions or subclasses of Actor"

            if isactor(function_or_actor):
                self.log("Already is Actor. Creating Node")
                node = createNodeFromActor(function_or_actor, allow_empty_doc=allow_empty_doc, widgets=widgets)
            else:
                self.log("Is Function. Creating Node and Wrapping")
                node = createNodeFromFunction(function_or_actor, allow_empty_doc=allow_empty_doc, widgets=widgets)

            # We pass this down to our truly template wrapper that takes the node and transforms it
            template_wrapper = self.template(node, **implementation_details)
            function = template_wrapper(function_or_actor)
            return function

        return real_decorator


    @abstractmethod
    async def connect(self) -> str:
        raise NotImplementedError("Please overwrite")

    @abstractmethod
    async def disconnect(self) -> str:
        raise NotImplementedError("Please overwrite")


    @abstractmethod
    async def forward(self, message: MessageModel) -> None:
        raise NotImplementedError("Please overwrite")


    async def on_message(self, message: MessageModel):
        await self.message_queue.put(message)


    async def handle_bounced_provide(self, message: BouncedProvideMessage):
        try:
            await self.on_bounced_provide(message)

            progress = ProvideLogMessage(data={
            "level": LogLevel.INFO,
            "message": f"Pod Pending"
            }, meta={"extensions": message.meta.extensions, "reference": message.meta.reference})

            await self.forward(progress)


        except Exception as e:
            logger.error(e)
            critical_error = ProvideCriticalMessage(data={
            "message": str(e),
            "type": e.__class__.__name__
            }, meta={"extensions": message.meta.extensions, "reference": message.meta.reference})
            await self.forward(critical_error)
            raise e


    async def handle_bounced_unprovide(self, message: BouncedUnprovideMessage):
        try:
            await self.on_bounced_unprovide(message)

            progress = UnprovideLogMessage(data={
            "level": LogLevel.INFO,
            "message": f"Pod Unproviding",
            "provision": message.data.provision,
            }, meta={"extensions": message.meta.extensions, "reference": message.meta.reference})

            await self.forward(progress)

        except Exception as e:
            logger.exception(e)
            critical_error = UnprovideCriticalMessage(data={
            "message": str(e),
            "type": str(e.__class__.__name__),
            "provision": message.data.provision,
            }, meta={"extensions": message.meta.extensions, "reference": message.meta.reference})

            await self.forward(critical_error)


    @hookable("bounced_provide", overwritable=True)
    async def on_bounced_provide(self, message: BouncedProvideMessage):
        actorClass = await self.get_actorclass_for_template(message.data.template)
        self.log(f"Got provision request for {message.data.template} and will entertain {actorClass.__name__}")
        await self.client.entertainer.entertain(message, actorClass) # Run in parallel

    @hookable("bounced_unprovide", overwritable=True)
    async def on_bounced_unprovide(self, message: BouncedUnprovideMessage):
        self.log(f"Got unprovision. Sending to entertainer")
        await self.client.entertainer.unentertain(message)

    @hookable("get_actorclass_for_template", overwritable=True)
    async def get_actorclass_for_template(self, template_id):
        assert template_id in self.template_actorClass_map, f"We have no Actor stored in our list for Template with ID {template_id}"
        return self.template_actorClass_map[template_id]

    def register_actor(self, template_id: str, actorClass: Type[Actor]):
        assert template_id not in self.template_actorClass_map, f"We cannot register two Actors for the same template {template_id}"
        self.template_actorClass_map[template_id] = actorClass
        self.log(f"Registered Actor {actorClass.__name__} for Template {template_id}")

    async def provide_async(self):

        self.log(" ------------- AWAITING MESSAGES -----------")
        while True:
            message = await self.message_queue.get()
            
            if isinstance(message, BouncedProvideMessage):
                logger.info("Received Provide Request")
                assert message.data.template is not None, "Received Provision that had no Template???"
                await self.handle_bounced_provide(message)

            elif isinstance(message, BouncedUnprovideMessage):
                logger.info("Received Unprovide Request")
                assert message.data.provision is not None, "Received Unprovision that had no Provision???"
                await self.handle_bounced_unprovide(message)
            else: 
                self.log(f"Provider: [red] Received unknown message {message}")

            self.message_queue.task_done()

            
    def provide(self):
        if self.loop.is_running():
            raise Exception("Cannot do this in a running loop, please await or create task of provide_async()")
        else:
            self.loop.run_until_complete(self.provide_async())

        # we enter a never-ending loop that waits for data
        # and runs callbacks whenever necessary.
        

