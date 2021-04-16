from bergen.actors.utils import log
from bergen.clients.provider import ProviderBergen
from bergen.provider.base import OneExlusivePodPolicy
import asyncio
import logging


logger = logging.getLogger(__name__)

client = ProviderBergen(
        config_path="nana.yaml",
        force_new_token=True,
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)


@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
async def adder(x: int, y: int, z: int = 7) -> int:
        """Adder

        Adds x + y

        Args:
            x (int): Input X
            y (int): Input Y

        Returns:
            int: X + Y
        """
        return x + y



    
@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
async def constantadder(x: int, z: int = 7) -> int:
        """Constant Adder

        Adds a constant number to x, (will result to a constant value of 7 if no constant is set)

        Args:
            x (int): Input X
            z (int, optional): Input Z (Defaults to: 7)

        Returns:
            int: X + Z
        """
        return x + z



@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
async def sleeper(sleep: int, amount: int = 5) -> int:
        """Sleeper

        Sleeps an interval of time {sleep} and then returns the current iteration until a total of {amount} steps

        Args:
            sleep (int): The amount of time you are going to sleep
            amount (int, optional): The amount of intervals (Defaults to: 5)

        Returns:
            int: X + Y
        """
        for i in range(0,amount):
            print("yielding")
            yield i
            await asyncio.sleep(3)
            await log("Yielding")
            #await asyncio.sleep(0.01 * sleep)


client.provide()