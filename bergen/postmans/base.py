from abc import ABC, abstractmethod
from aiostream import stream


class BasePostman(ABC):
    """ A Postman takes node requests and translates them to Bergen calls, basic implementations are GRAPHQL and PIKA"""

    def __init__(self, requires_configuration=True, loop=None) -> None:
        assert loop is not None, "Please provide a Loop to your Postman, Did you forget to call super.init with **kwargs?"
        self.loop = loop

    @abstractmethod
    async def configure(self):
        pass

    @abstractmethod
    def stream(inputs: dict, params: dict, **kwargs):
        return NotImplementedError( "Abstract class")


    @abstractmethod
    async def assign(self, inputs: dict, params: dict, **kwargs):

        return NotImplementedError("This is abstract")

    @abstractmethod
    async def provide(self, inputs: dict, params: dict, **kwargs):

        return NotImplementedError("This is abstract")

    @abstractmethod
    async def delay(self, inputs: dict, params: dict, **kwargs):

        return NotImplementedError("This is abstract")



