from bergen.schema import Template
from bergen.messages.postman.assign.assign_done import AssignDoneMessage
from bergen.debugging import DebugLevel
from bergen.handlers.base import ContractHandler
from bergen.messages import BouncedProvideMessage
from bergen.console import console


class ProvideHandler(ContractHandler[BouncedProvideMessage]):

    @property
    def template_id(self) -> str:
        return self.message.data.template

    async def get_template(self) -> Template:
        return await Template.asyncs.get(id=self.message.data.template)


    async def pass_exception(self, exception):
        console.print_exception()