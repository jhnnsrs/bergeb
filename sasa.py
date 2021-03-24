from bergen.clients.provider import ProviderBergen
from bergen.entertainer.actor import AsyncFuncActor
from bergen.provider.base import OneExlusivePodPolicy
import asyncio
import logging

logger = logging.getLogger(__name__)

client = ProviderBergen(
        name="sasa",
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)

@client.enable(gpu=True, policy=OneExlusivePodPolicy())
class Adder(AsyncFuncActor):
    
    async def reserve(self):
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
        await asyncio.sleep(1)
        return x + y


    async def unreserve(self):
        logger.info("Unreserve")


client.provide()