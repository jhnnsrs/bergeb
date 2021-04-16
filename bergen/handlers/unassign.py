from typing import Union
from bergen.debugging import DebugLevel
from bergen.handlers.base import ContractHandler
from bergen.messages import BouncedUnassignMessage, UnassignDoneMessage, UnassignCriticalMessage
from bergen.console import console


class UnassignHandler(ContractHandler[BouncedUnassignMessage]):

    async def log(self, message, level=DebugLevel.INFO):
        await self.connection.forward(message)

    @property
    def meta(self):
        return {"extensions": self.message.meta.extensions, "reference": self.message.meta.reference}

    async def pass_progress(self, text: str = None, percentage: int = None):
        console.log(text + percentage)

    async def pass_done(self):
        error_message = UnassignDoneMessage(data={"assignation": self.message.data.assignation}, meta=self.meta)
        await self.forward(error_message)

    async def pass_exception(self, message: BouncedUnassignMessage, exception: Union[Exception,str]):
        error_message = UnassignCriticalMessage(data={"message": str(exception), "type": exception.__class__.__name__}, meta=self.meta)
        await self.forward(error_message)
