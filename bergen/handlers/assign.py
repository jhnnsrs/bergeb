from bergen.messages.postman.assign.assign_cancelled import AssignCancelledMessage
from bergen.messages.postman.log import LogLevel
from bergen.debugging import DebugLevel
from bergen.handlers.base import ContractHandler
from bergen.messages import BouncedForwardedAssignMessage, AssignYieldsMessage, AssignLogMessage, AssignDoneMessage, AssignReturnMessage, AssignCriticalMessage
from bergen.console import console


class AssignHandler(ContractHandler[BouncedForwardedAssignMessage]):

    @property
    def meta(self):
        return {"extensions": self.message.meta.extensions, "reference": self.message.meta.reference}

    async def log(self, message, level =LogLevel.INFO):
        console.log(message)
        await self.pass_log(str(message), level=level)

    async def pass_yield(self, value):
        yield_message = AssignYieldsMessage(data={"returns": value}, meta=self.meta)
        await self.forward(yield_message)

    async def pass_log(self, message: str, level: LogLevel = LogLevel.INFO):
        progress_message = AssignLogMessage(data={"message": message, "level": level.value}, meta=self.meta)
        await self.forward(progress_message)

    async def pass_done(self):
        return_message = AssignDoneMessage(data={"ok": True}, meta=self.meta)
        await self.forward(return_message)

    async def pass_cancelled(self):
        return_message = AssignCancelledMessage(data={"ok": True}, meta=self.meta)
        await self.forward(return_message)

    async def pass_result(self, value):
        return_message = AssignReturnMessage(data={"returns": value}, meta=self.meta)
        await self.forward(return_message)

    async def pass_exception(self, exception):
        console.print_exception()
        error_message = AssignCriticalMessage(data={"message": str(exception), "type": str(exception.__class__.__name__)}, meta=self.meta)
        await self.forward(error_message)