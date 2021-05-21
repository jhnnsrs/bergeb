from bergen.messages.postman.unprovide.unprovide_critical import UnprovideCriticalMessage
from bergen.messages.postman.unprovide.unprovide_log import UnprovideLogMessage
from bergen.messages.postman.log import LogLevel, LogDataModel
from bergen.messages.postman.unprovide.unprovide_done import UnprovideDoneMessage
from bergen.messages.postman.unprovide.bounced_unprovide import BouncedUnprovideMessage
from bergen.messages.postman.unreserve.unreserve_critical import UnreserveCriticalMessage
from bergen.messages.postman.reserve.reserve_critical import ReserveCriticalMessage
from bergen.schema import Template
from bergen.messages.postman.assign.assign_done import AssignDoneMessage
from bergen.debugging import DebugLevel
from bergen.handlers.base import ContractHandler
from bergen.messages import BouncedUnreserveMessage
from bergen.console import console


class UnprovideHandler(ContractHandler[BouncedUnprovideMessage]):

    @property
    def bounced(self):
        return self.message.meta.token

    @property
    def meta(self):
        return {"extensions": self.message.meta.extensions, "reference": self.message.meta.reference}

    async def pass_log(self, message, level=LogLevel.INFO):
        log_message = UnprovideLogMessage(data={"message": message, "level": level, "provision": self.message.data.provision}, meta=self.meta)
        return await self.connection.forward(log_message)   

    async def pass_done(self):
        done_message = UnprovideDoneMessage(data={"provision": self.message.data.provision}, meta=self.meta)
        return await self.connection.forward(done_message) #Contrary to a Done signal we are the provision just to the backend, because it will take care of it

    async def pass_error(self, exception):
        critical_message = UnprovideErrorMessage(data={"message": str(exception), "type": exception.__class__.__name__}, meta=self.meta)
        console.print_exception()
        return await self.connection.forward(critical_message)

    async def pass_critical(self, exception):
        critical_message = UnprovideCriticalMessage(data={"message": str(exception), "type": exception.__class__.__name__}, meta=self.meta)
        console.print_exception()
        return await self.connection.forward(critical_message)
