from typing import Any
from bergen.messages.postman.reserve.reserve_critical import ReserveCriticalMessage
from bergen.schema import Template
from bergen.messages.postman.assign.assign_done import AssignDoneMessage
from bergen.debugging import DebugLevel
from bergen.handlers.base import Connector, ContractHandler
from bergen.messages import BouncedForwardedReserveMessage
from bergen.console import console


class ReserveHandler(ContractHandler[BouncedForwardedReserveMessage]):

    def __init__(self, message: BouncedForwardedReserveMessage, connection: Connector) -> None:
        super().__init__(message, connection)
        self.active_context = None
        self.context_set = False

    @property
    def bounced(self):
        return self.message.meta.token

    @property
    def meta(self):
        return {"extensions": self.message.meta.extensions, "reference": self.message.meta.reference}

    @property
    def template_id(self) -> str:
        return self.message.data.template

    @property
    def context(self) -> Any:
        assert self.context_set, "Context was never set, no sense in accessing it..."
        return self.active_context   


    def set_context(self, context):
        self.context_set = True
        self.active_context = context

    async def get_template(self) -> Template:
        return await Template.asyncs.get(id=self.message.data.template)

    async def pass_done(self):
        return await self.connection.forward(self.message) #Contrary to a Done signal we are the provision just to the backend, because it will take care of it

    async def pass_exception(self, exception):
        critical_message = ReserveCriticalMessage(data={"message": str(exception), "type": exception.__class__.__name__}, meta=self.meta)
        console.print_exception()
        return await self.connection.forward(critical_message)
