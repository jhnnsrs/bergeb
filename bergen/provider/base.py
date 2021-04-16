from abc import abstractmethod
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
from bergen.models import Node
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


    def __init__(self, *args, provider: int = None, loop=None, client: BaseBergen =None, **kwargs) -> None:
        super().__init__(**kwargs)
        assert provider is not None, "Provider was set to none, this is weird!!"
        self.arkitekt_provider = provider
        self.client = client
        self.loop = loop or asyncio.get_event_loop()

        self.template_actorClass_map = {}

        self.provisions = {}
        self.auto_provided_templates = [] # Templates that this provide will try to provide on startup


    def template(self, node: Node, policy: PodPolicy = MultiplePodPolicy(), auto_provide=False, on_provide=None,  on_unprovide=None, **implementation_details):

        def real_decorator(function_or_actor):
            assert callable(function_or_actor) or issubclass(function_or_actor, Actor), "Please only decorate functions or subclasses of Actor"
            # TODO: Check if function has same parameters as node

            template = OFFER_GQL.run(
            ward=self.client.main_ward,
            variables= {
                "node": node.id,
                "params": implementation_details,
                "policy": policy.dict()
            })


            if isactor(function_or_actor):
                actorClass = function_or_actor
            else:
                is_coroutine = inspect.iscoroutinefunction(function_or_actor)
                is_asyncgen = inspect.isasyncgenfunction(function_or_actor)
                is_function = inspect.isfunction(function_or_actor)

                if is_coroutine:
                    actorClass =  type(f"GeneratedActor{template.id}",(FunctionalFuncActor,), {"assign": staticmethod(function_or_actor)})
                elif is_asyncgen:
                    actorClass =  type(f"GeneratedActor{template.id}",(FunctionalGenActor,), {"assign": staticmethod(function_or_actor)})
                elif is_function:
                    actorClass = type(f"GeneratedActor{template.id}",(FunctionalThreadedFuncActor,), {"assign": staticmethod(function_or_actor)})
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
                console.log("Already is Actor. Creating Node")
                node = createNodeFromActor(function_or_actor, allow_empty_doc=allow_empty_doc, widgets=widgets)
            else:
                console.log("Is Function. Creating Node and Wrapping")
                node = createNodeFromFunction(function_or_actor, allow_empty_doc=allow_empty_doc, widgets=widgets)

            console.log("Created Node",node)
                
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
        if isinstance(message, BouncedProvideMessage):
            logger.info("Received Provide Request")
            assert message.data.template is not None, "Received Provision that had no Template???"
            await self.handle_bounced_provide(message)

        elif isinstance(message, BouncedUnprovideMessage):
            logger.info("Received Unprovide Request")
            assert message.data.provision is not None, "Received Unprovision that had no Provision???"
            await self.handle_bounced_unprovide(message)

        else: 
            raise Exception("Received Unknown Task")


    async def handle_bounced_provide(self, message: BouncedProvideMessage):
        try:
            await self.on_bounced_provide(message)

            progress = ProvideProgressMessage(data={
            "level": "INFO",
            "message": f"Pod Pending"
            }, meta={"extensions": message.meta.extensions, "reference": message.meta.reference})

            await self.forward(progress)
        except Exception as e:
            logger.error(e)
            critical_error = ProvideCriticalMessage(data={
            "message": str(e)
            }, meta={"extensions": message.meta.extensions, "reference": message.meta.reference})
            await self.forward(critical_error)
            raise e

    async def handle_bounced_unprovide(self, message: BouncedProvideMessage):
        try:
            await self.on_bounced_unprovide(message)

            progress = UnprovideProgressMessage(data={
            "level": "INFO",
            "message": f"Pod Unproviding"
            }, meta={"extensions": message.meta.extensions, "reference": message.meta.reference})

            await self.forward(progress)

        except Exception as e:
            logger.error(e)
            critical_error = UnprovideCriticalMessage(data={
            "message": str(e)
            }, meta={"extensions": message.meta.extensions, "reference": message.meta.reference})

            await self.forward(critical_error)


    @hookable("bounced_provide", overwritable=True)
    async def on_bounced_provide(self, message: BouncedProvideMessage):
        actorClass = await self.get_actorclass_for_template(message.data.template)
        console.log(f"[red]Got provision request for {message.data.template} and will entertain {actorClass.__name__}")
        await self.client.entertainer.entertain(message, actorClass) # Run in parallel

    @hookable("bounced_unprovide", overwritable=True)
    async def on_bounced_unprovide(self, message: BouncedUnprovideMessage):
        console.log(f"[red]Got unprovision. Sending to entertainer")
        await self.client.entertainer.unentertain(message)

    @hookable("get_actorclass_for_template", overwritable=True)
    async def get_actorclass_for_template(self, template_id):
        assert template_id in self.template_actorClass_map, f"We have no Actor stored in our list {template_id}"
        return self.template_actorClass_map[template_id]

    def register_actor(self, template_id: str, actorClass: Type[Actor]):
        assert template_id not in self.template_actorClass_map, f"We cannot register two Actors for the same template {template_id}"
        self.template_actorClass_map[template_id] = actorClass
        console.log(f"[red]Registered Actor {actorClass.__name__} for Template {template_id}")

    async def provide_async(self):
        while True:
            await asyncio.sleep(3)

    def provide(self):
        if self.loop.is_running():
            logger.error("Cannot do this, please await run()")
        else:
            self.loop.run_forever()

        # we enter a never-ending loop that waits for data
        # and runs callbacks whenever necessary.
        

