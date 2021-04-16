import asyncio
from abc import ABC, abstractmethod
from asyncio.futures import Future
from bergen.handlers.base import Connector
from bergen.messages import *
from bergen.hookable.base import Hookable
import logging
from typing import Dict, Type
from bergen.models import Pod
from bergen.actors.base import Actor
from functools import partial
from bergen.console import console



logger = logging.getLogger(__name__)



class BaseEntertainer(Hookable):
    ''' Is a mixin for Our Bergen '''
    def __init__(self, raise_exceptions_local=False, client = None, loop=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.provisions = {}
        self.raise_exceptions_local = raise_exceptions_local
        self.loop = loop or asyncio.get_event_loop()
        self.client = client

        self.connector = Connector(self)

        self.template_id_actorClass_map: Dict[str, Type[Actor]] = {}

        self.provision_actor_map: Dict[str, Actor] = {}
        self.provision_actor_run_map: Dict[str, asyncio.Task]= {}
        self.provision_actor_queue_map: Dict[str, asyncio.Queue] = {}


        self.unprovide_futures: Dict[str, Future] = {}
        self.provide_futures: Dict[str, Future] = {}

        self.all_pod_assignments = {}
        self.all_pod_reservations = {}

        self.entertainments = {}
        self.assignments = {}

        self.pending = []

        self.tasks = []

    @abstractmethod
    async def connect(self) -> str:
        raise NotImplementedError("Please overwrite")

    @abstractmethod
    async def disconnect(self) -> str:
        raise NotImplementedError("Please overwrite")

    @abstractmethod
    async def activateProvision(self):
         raise NotImplementedError("Please overwrite")

    @abstractmethod
    async def deactivateProvision(self):
         raise NotImplementedError("Please overwrite")

    @abstractmethod
    async def forward(self, message: MessageModel):
        raise NotImplementedError("Overwrite this in your Protocol")


    async def on_message(self, message: MessageModel):
        
        if isinstance(message, ProvideDoneMessage): 
            # As we send the Activate Provide request to the Platform we will get a Return Statement
            logger.info("Arkitekt acknowledged the creation of a Pod for our Actor [this has no consequences??]")
            self.provide_futures[message.meta.reference].set_result(message.data.pod)

        if isinstance(message, UnprovideDoneMessage): 
            # As we send the Activate Provide request to the Platform we will get a Return Statement
            logger.info("Arkitekt acknowledged the deletion of the Pod our our former Actor")
            self.unprovide_futures[message.meta.reference].set_result(message.data)

        if isinstance(message, BouncedUnprovideMessage): 
            #  We are responsible To Shut ourselfves down when Arkitekt Tells us t
            assert message.data.provision is not None, "Received Cancellation with no reference to kill" 
            self.unentertain(message, from_arkitekt=True)

        if isinstance(message, BouncedProvideMessage): 
            #  We are responsible To Shut ourselfves down when Arkitekt Tells us t
            assert message.data.template is not None, "Received Cancellation with no reference to kill" 
            logger.info("Arkitekt demands a New Actor for us")
            self.entertain(message, from_arkitekt=True)

        if isinstance(message, BouncedForwardedReserveMessage):
            logger.info("Arkitekt demands a New Reservation from us")
            assert message.data.provision is not None, "Received Forwared Reservation that had no Provision???"
            assert message.data.provision in self.provision_actor_queue_map, f"Provision not entertained {message.data.provision} {self.provision_actor_queue_map}"
            await self.provision_actor_queue_map[message.data.provision].put(message)
            self.all_pod_reservations[message.meta.reference] = message.data.provision # Run in parallel

        if isinstance(message, BouncedUnreserveMessage):
            if message.data.reservation in self.all_pod_reservations: 
                logger.info("Cancellation for Reservatoion received. Canceling!")
                hosting_provising = self.all_pod_reservations[message.data.reservation]
                await self.provision_actor_queue_map[hosting_provising].put(message)
            else:
                logger.error("Received Cancellation for task that was not in our tasks..")


        if isinstance(message, BouncedForwardedAssignMessage):
            assert message.data.provision is not None, "Received assignation that had no Provision???"
            assert message.data.provision in self.provision_actor_queue_map, f"Provision not entertained {message.data.provision} {self.provision_actor_queue_map}"
            await self.provision_actor_queue_map[message.data.provision].put(message)
            self.all_pod_assignments[message.meta.reference] = message.data.provision # Run in parallel

        if isinstance(message, BouncedUnassignMessage):
            if message.data.assignation in self.all_pod_assignments: 
                logger.info("Cancellation for task received. Canceling!")
                hosting_provising = self.all_pod_assignments[message.data.assignation]
                await self.provision_actor_queue_map[hosting_provising].put(message)
            else:
                logger.error("Received Cancellation for task that was not in our tasks..")


    async def deactivateProvision(self, bounced_unprovide: BouncedUnprovideMessage):
        # Where should we do this?
        future = self.loop.create_future()
        self.unprovide_futures[bounced_unprovide.meta.reference] = future
        await self.forward(bounced_unprovide)
        reference = await future # is just a loopback??
        return reference

    async def activateProvision(self, bounced_provide: BouncedProvideMessage):
        
        #We are forwarding the Provision to Arkitekt and wait for its acknowledgement of the creation of this Pod
        future = self.loop.create_future()
        self.provide_futures[bounced_provide.meta.reference] = future
        await self.forward(bounced_provide)
        id = await future
        pod = await Pod.asyncs.get(id=id)
        return pod

    
    def actor_cancelled(self, actor: Actor, future: Future):
        logger.info("Actor is done! Cancellation or Finished??")
        if future.cancelled():
            logger.info("Future was cancelled everything is cools")


    async def get_actorclass_for_template(self, template_id):
        assert template_id in self.template_id_actorClass_map, "We have no Actor stored in our list"
        return self.template_id_actorClass_map[template_id]


    def registerActor(self, template_id: str, actorClass: Type[Actor]):
        assert template_id not in self.template_id_actorClass_map, "We cannot register two Actors for the same template on the same provider"
        self.template_id_actorClass_map[template_id] = actorClass


    async def unentertain(self, bounced_unprovide: BouncedUnprovideMessage, from_arkitekt=False):
        if from_arkitekt: logger.info("Cancellation invoked by Arkitekt")

        provision_reference = bounced_unprovide.data.provision
        deactivation_task = asyncio.create_task(self.deactivateProvision(bounced_unprovide))
        deactivation_task.add_done_callback(print)   

        task = self.provision_actor_run_map[provision_reference]

        if not task.done():
            logger.info("Cancelling Task")
            task.cancel()


        
        
        # THIS Comes form the Arkitekt Platform

    
    async def entertain(self, bounced_provide: BouncedProvideMessage, actorClass: Type[Actor], from_arkitekt=False):
        ''' Takes an instance of a pod, asks arnheim to activate it and accepts requests on it,
        cancel this task to unprovide your local implementatoin '''
        if from_arkitekt: logger.info("Entertainment invoked by Arkitekt")

        provision_reference = bounced_provide.meta.reference # We register Actors unter its provision
        actor = actorClass(self.connector)

        try:
            # Activate Provison , will return
            activation_task = asyncio.create_task(self.activateProvision(bounced_provide))
            activation_task.add_done_callback(print)

            self.provision_actor_map[provision_reference] = actor
            self.provision_actor_queue_map[provision_reference] = actor.queue
            run_task = asyncio.create_task(actor.run(bounced_provide))
            run_task.add_done_callback(partial(self.actor_cancelled, actor))
            self.provision_actor_run_map[provision_reference] = run_task

        except Exception as e:
            logger.error("We have a provision error")
            logger.error(e)
            # This error gets passed back to the provider
            raise e


