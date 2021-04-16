from bergen.messages.postman.unreserve.unreserve_critical import UnreserveCriticalMessage
from bergen.messages.postman.reserve.reserve_critical import ReserveCriticalMessage
from bergen.schema import Template
from bergen.messages.postman.assign.assign_done import AssignDoneMessage
from bergen.debugging import DebugLevel
from bergen.handlers.base import ContractHandler
from bergen.messages import BouncedUnreserveMessage
from bergen.console import console


class UnreserveHandler(ContractHandler[BouncedUnreserveMessage]):

    @property
    def bounced(self):
        return self.message.meta.token

    @property
    def meta(self):
        return {"extensions": self.message.meta.extensions, "reference": self.message.meta.reference}

    async def pass_done(self):
        return await self.connection.forward(self.message) #Contrary to a Done signal we are the provision just to the backend, because it will take care of it

    async def pass_exception(self, exception):
        critical_message = UnreserveCriticalMessage(data={"message": str(exception), "type": exception.__class__.__name__}, meta=self.meta)
        console.print_exception()
        return await self.connection.forward(critical_message)
