from bergen.messages.postman import provide
from bergen.messages.postman.provide import BouncedProvideMessage
from bergen.clients.provider import ProviderBergen
from bergen.entertainer.actor import AsyncFuncActor
from bergen.provider.base import BaseProvider, OneExlusivePodPolicy
import asyncio
import logging

logger = logging.getLogger(__name__)

client = ProviderBergen(
        config_path="nana.yaml",
        force_new_token=True,
        name="ImageJ",
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)


async def spawnDockerForProvide(template_id):
    return True



@client.hook("bounced_provide", overwrite=True)
async def on_bounced_provide(self: BaseProvider, bounced_provide: BouncedProvideMessage):

    await spawnDockerForProvide(bounced_provide.data.template)

    
    #   





    # The Entertain path (in same process or on VM???)
    self.client.entertainer.entertain(bounced_provide, NewAdder)

    logger.error("Nana")




@client.enable(gpu=True, policy=OneExlusivePodPolicy())
class NewAdder(AsyncFuncActor):
    
    async def on_provide(self):
        logger.info("Reserving")

    async def assign(self, x: int, y: int, z: int = 7) -> int:
        """Adder

        Adds x + y

        Args:
            helper ([type]): [description]
            x (int): Input X
            y (int): Input Y

        Returns:
            int: X + Y
        """
        return x + y


    async def on_unprovide(self):
        logger.info("Unreserve")


client.provide()