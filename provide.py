from bergen.actors.utils import log
from bergen.clients.provider import ProviderBergen
from bergen.provider.base import OneExlusivePodPolicy
import asyncio
import logging
import random
import time

logger = logging.getLogger(__name__)

client = ProviderBergen(
        config_path = "bergen.yaml",
        log_stream = True,
        force_new_token=True,
        auto_reconnect=True #if we want to specifically only use pods on this innstance we would use that it in the selector
)

client.negotiate()


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
async def randomint(start: int = 0, end: int = 100) -> int:
    """Random Integer

    Returns a random integer between {start} and {end}

    Args:
        start (int, optional): Start of range. Defaults to 0.
        end (int, optional): End of range. Defaults to 100.

    Returns:
        int: A Random integer
    """
    await log(f"Sleeping Super Fast")
    await asyncio.sleep(1)

    return random.randint(0, 100)



@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
async def intyielder(interval: int= 1, iterations: int = 6) -> int:
    """Int Yielder

    Yields an increasing integer every {interval} seconds for {iterations} Iterations

    Args:
        interval (int, optional): the interval to sleep. Defaults to 1.
        iterations (int, optional): the iterations this loop undergoes. Defaults to 6.

    Returns:
        int: An increasing Integer
    """
        
    for i in range(0,iterations):

        await log(f"Sleeping {interval}")
        await asyncio.sleep(interval)
        await log(f"Yielding {i}")
        yield i


@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
async def camille_cool_function(x: int, y: int, cool: int = 5) -> int:
    """Cammiles Cool FUnction

    Camilles function takes somthing aoinsoinsoinse

    Args:
        x (int): sdf
        y (int): sdfsdf
        cool (int, optional): sdfsdf. Defaults to "Hallo".

    Returns:
        int: sdfsdf
    """

    return x + y

@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
def threaded_function(x: int, y: int, cool: int = 5) -> int:
    """Threaded funciton

    Camilles function takes somthing aoinsoinsoinse

    Args:
        x (int): sdf
        y (int): sdfsdf
        cool (int, optional): sdfsdf. Defaults to "Hallo".

    Returns:
        int: sdfsdf
    """
    log("nananana")
    print("Done")
    time.sleep(4)
    print("Run")

    return x + y

@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
async def call_me(cool: int = 5) -> int:
    """Call me

    Camilles function takes somthing aoinsoinsoinse

    Args:
        cool (int, optional): sdfsdf. Defaults to 5.

    Returns:
        int: sdfsdf
    """
    await log("nananana")
    print("Done")
    await asyncio.sleep(4)
    print("Run")

    return cool


@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
def call_me_threaded(cool: int = 5) -> int:
    """Call me threaded

    Camilles function takes somthing aoinsoinsoinse

    Args:
        cool (int, optional): sdfsdf. Defaults to 5.

    Returns:
        int: sdfsdf
    """
    log("nananana")
    print("Done")
    time.sleep(4)
    print("Run")

    return cool


@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
def maxisp_projectio(cool: int = 5) -> int:
    """Maximum Intensity Projection

    Makes a meaximun intensity projection

    Args:
        cool (int, optional): sdfsdf. Defaults to 5.

    Returns:
        int: sdfsdf
    """
    log("nananana")
    print("Done")
    time.sleep(3)
    print("Run")

    return cool









client.provide()