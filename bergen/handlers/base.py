

from abc import ABC, abstractmethod
from bergen.messages.base import MessageModel
from bergen.debugging import DebugLevel, get_style_for_level
from typing import Generic, TypeVar
from bergen.console import console

T = TypeVar("T")

class Connector(ABC):

    def __init__(self, connection) -> None:
        self.connection = connection

    async def forward(self, message: MessageModel):
        await self.connection.forward(message)




class ContractHandler(Generic[T]):

    def __init__(self, message: T, connection: Connector) -> None:
        self.message = message
        self.connection = connection

    async def log(self, message, level: DebugLevel = DebugLevel.INFO):
        console.log(get_style_for_level(level) + level.value + " : ", message)
    

    async def forward(self, message):
        await self.connection.forward(message)


    