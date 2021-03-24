import asyncio
from abc import ABC, abstractmethod
from asyncio.futures import Future
import logging
from typing import Dict, Type
from bergen.models import Pod
from .actor import Actor, HostHelper
from functools import partial
import uuid

logger = logging.getLogger(__name__)

class BaseHost(ABC):
    ''' Is a mixin for Our Bergen '''
    helperClass = None

    def __init__(self, raise_exceptions_local=False, client = None, loop=None,**kwargs) -> None:
        self.pods = {}
        self.raise_exceptions_local = raise_exceptions_local
        self.loop = loop or asyncio.get_event_loop()
        self.client = client

        self.hostHelper = self.helperClass(self)

        self.pod_actor_run_map: Dict[str, asyncio.Task]= {}
        self.pod_actor_queue_map: Dict[str, asyncio.Queue] = {}

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
    async def activatePod(self):
         raise NotImplementedError("Please overwrite")

    @abstractmethod
    async def deactivatePod(self):
         raise NotImplementedError("Please overwrite")

    async def unentertain(self, pod_id: str):
        assert pod_id not in self.pod_actor_run_map, "This actor is not entertained"
        task = self.pod_actor_run_map.pop(pod_id)
        if task.done():
            raise Exception("Task was already done, this is weird")
        elif task.exception():
            logger.info("Task already was cancelled apparently")
        else:
            task.cancel()
    

    def actor_cancelled(self, actor: Actor, future: Future):
        logger.info("Actor is done! Cancellation or Finished??")
        if future.exception():
            raise future.exception()


        self.tasks.append(asyncio.create_task(self.deactivatePod(actor.pod)))

    async def entertain(self, pod: Pod, actorClass: Type[Actor]):
        ''' Takes an instance of a pod, asks arnheim to activate it and accepts requests on it,
        cancel this task to unprovide your local implementatoin '''
        assert pod.id not in self.pod_actor_run_map, "This pod is already entertained"

        reference = str(uuid.uuid4())
        actor = actorClass(pod, self.hostHelper)
        await self.activatePod(pod, reference)

        try:
            self.pod_actor_queue_map[str(pod.id)] = actor.queue
            run_task = asyncio.create_task(actor.run())
            run_task.add_done_callback(partial(self.actor_cancelled, actor))
            self.pod_actor_run_map[str(pod.id)] = run_task

        except Exception as e:
            logger.error(e)

