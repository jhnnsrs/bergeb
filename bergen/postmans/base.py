from abc import ABC, abstractmethod
from bergen.hookable.base import Hookable
from bergen.schema import Node, Pod
from typing import Callable
from aiostream import stream
import asyncio

class BasePostman(Hookable):
    """ A Postman takes node requests and translates them to Bergen calls, basic implementations are GRAPHQL and PIKA"""

    def __init__(self, requires_configuration=True, loop=None, client=None, **kwargs) -> None:
        super().__init__(**kwargs)
        assert loop is not None, "Please provide a Loop to your Postman, Did you forget to call super.init with **kwargs?"
        self.loop = loop or asyncio.get_event_loop()
        self.client = client

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def stream(self, node: Node = None, pod: Pod = None, args = None, kwargs = None, params= None, on_progress: Callable = None):
        return NotImplementedError( "Abstract class")

    @abstractmethod
    async def assign(self, node: Node = None, pod: Pod = None, reservation: str = None,  args = None, kwargs = None, params= None, on_progress: Callable = None):
        return NotImplementedError("This is abstract")

    @abstractmethod
    async def provide(self, *args, **kwargs):
        return NotImplementedError("This is abstract")

    @abstractmethod
    async def unprovide(self, *args, **kwargs):
        return NotImplementedError("This is abstract")




