from bergen.provider.base import OneExlusivePodPolicy
from typing import Tuple
from bergen.clients.provider import ProviderBergen
import asyncio

client = ProviderBergen(
        name="sasa",
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)


@client.enable(gpu=True, 
    policy=OneExlusivePodPolicy(),
    auto_provide=True,
    on_provide=lambda x: print("On Provide")
)
async def timer(helper, interval: int = 5) -> int:
    """Timer Timer

    Timer timer does what is wnats

    Args:
        helper ([type]): [description]
        interval (int, optional): The Interval in seconds. Defaults to 5.

    Returns:
        int: The Passed Time in seconds

    """
    
    number = 0
    while True:
        asyncio.sleep(interval)
        yield number
        number += 1


    
@client.enable(gpu=True, 
    auto_provide=True,
    on_provide=lambda x: print("On Provide")
)
async def adder(helper, x: int, y: int) -> int:
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



client.provide()