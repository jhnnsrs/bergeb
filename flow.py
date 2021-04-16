
from flow.actors.func_flow import FuncFlowActor

from bergen.provider.base import BaseProvider
from bergen.clients.provider import ProviderBergen
import asyncio
import logging
logger = logging.getLogger(__name__)



async def main():

    async with ProviderBergen(
        config_path="fluss.yaml",
        name="Fluss",
        force_new_token=True,
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
    ) as client:


        @client.hook("get_actorclass_for_template", overwrite=True)
        def get_actorclass_for_template(self: BaseProvider, template_id):
            print("hoainoainoainaoin")
            return FuncFlowActor

        await client.provide_async()



asyncio.run(main())
