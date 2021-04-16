from bergen.messages.postman.unprovide import BouncedUnprovideMessage
from bergen.messages.postman.provide import BouncedProvideMessage
from bergen.clients.provider import ProviderBergen
from bergen.entertainer.actor import AsyncFuncActor
from bergen.provider.base import BaseProvider, OneExlusivePodPolicy
import asyncio
import logging
from bergen.console import console
import json
logger = logging.getLogger(__name__)

client = ProviderBergen(
        config_path="nana.yaml",
        force_new_token=True,
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)


class OverWrittenAdder(AsyncFuncActor):

    async def on_provide(self):
        console.log("Reserving")

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
        await self.progress("Nintey Percent", 90)
        await asyncio.sleep(3)
        return x + y


    async def on_unprovide(self):
        console.log("Unproviding")


tasks = {}


client.entertainer.registerActor("6", OverWrittenAdder)


@client.hook("bounced_provide", overwrite=True)
async def on_bounced_provide(self: BaseProvider, bounced_provide: BouncedProvideMessage):

    reference = await client.entertainer.entertain(bounced_provide)

@client.hook("bounced_unprovide", overwrite=True)
async def on_bounced_unprovide(self: BaseProvider, bounced_unprovide: BouncedUnprovideMessage):

    await client.entertainer.unentertain(bounced_unprovide)



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