from bergen.contracts import reservation
from bergen.messages.postman.reserve.reserve_transition import ReserveState
from bergen.messages.postman.provide.provide_transition import ProvideState
from bergen.console import console
from bergen.handlers.provide import ProvideHandler
from bergen.comfort import use
from bergen.handlers.assign import AssignHandler
from bergen.actors.classic import ClassicFuncActor
from bergen.actors.utils import log, useApp, useUser
from bergen.clients.provider import ProviderBergen
from bergen.provider.base import OneExlusivePodPolicy
import asyncio
import logging
import random
import time

logger = logging.getLogger(__name__)

client = ProviderBergen(
        config_path = "implicit.yaml",
        log_stream = True,
        force_new_token=True,
        auto_reconnect=True #if we want to specifically only use pods on this innstance we would use that it in the selector
)

client.negotiate()


@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
def adder(x: int, y: int, z: int = 7) -> int:
        """Adder

        Adds x + y

        Args:
            x (int): Input X
            y (int): Input Y

        Returns:
            int: X + Y
        """
        print(useUser())
        print(useApp())
        return x + y


async def printer(x: int):
        """Printer

        Prints X

        Args:
            x (int): Input X
        """
        print(x)





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
    node = await use(package="Elements", interface="show")
    print(node)

    return random.randint(0, 100)



@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
def intyielder(interval: int= 1, iterations: int = 6) -> int:
    """Int Yielder

    Yields an increasing integer every {interval} seconds for {iterations} Iterations

    Args:
        interval (int, optional): the interval to sleep. Defaults to 1.
        iterations (int, optional): the iterations this loop undergoes. Defaults to 6.

    Returns:
        int: An increasing Integer
    """
        
    for i in range(0,iterations):
        print(f"Sleeping {interval}")
        time.sleep(interval)
        log(f"Yielding {i}")
        yield i


@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
def threaded_generatorddd(cool: int = 5) -> int:
    """Threaded Generator DD

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
    for i in range(3):
        time.sleep(1)
        print("Yield")

        yield cool

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


#@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
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
    print("Run")

    return cool


class TestProvider(ClassicFuncActor):

    async def change_state(self, seconds: int):
        try:
            while True:
                await asyncio.sleep(seconds)
                print("Changing State to INactive")
                await self.provide_handler.set_state(ProvideState.INACTIVE)
                await asyncio.sleep(seconds)
                print("Changing State to Active")
                await self.provide_handler.set_state(ProvideState.ACTIVE)
        except:
            console.print_exception()


    async def on_provide(self, provide: ProvideHandler):
        await provide.log("Providing Nodes")


    async def assign(self, assign_handler: AssignHandler, args, kwargs):
        """[summary]

        Args:
            assign_handler (AssignHandler): [description]
            args ([type]): [description]
            kwargs ([type]): [description]

        Returns:
            [type]: [description]
        """
        return args



class TestProvider(ClassicFuncActor):

    async def handle_reservation_change(self, res, status: str):
        self.current_state[res] = status
        errors = [ res.node for res, status in self.current_state.items() if status in [ReserveState.ERROR, ReserveState.CANCELLED]]
        if len(errors) > 0:
            print("We are now Unactive")
            await self.provide_handler.set_state(ProvideState.INACTIVE)
        else:
            print("We are now Active")
            await self.provide_handler.set_state(ProvideState.ACTIVE)

    async def on_provide(self, provide: ProvideHandler):
        await provide.log("Providing Nodes")

        self.current_state = {}
        print("Using", provide.reference)

        node = await use(package="Elements", interface="show")
        res = await node.reserve(provision=provide.reference).start(state_hook=self.handle_reservation_change)
        await provide.log(res)

        return {"task": res}


    async def assign(self, assign_handler: AssignHandler, args, kwargs):
        """[summary]

        Args:
            assign_handler (AssignHandler): [description]
            args ([type]): [description]
            kwargs ([type]): [description]

        Returns:
            [type]: [description]
        """
        return arg

    async def on_unprovide(self, handler: ProvideHandler):
        nana = handler.active_context
        await handler.log(f"Shutting Down {nana}")
        await asyncio.gather(*[res.end() for item, res in nana.items()])
        await handler.log("Shut down")




client.provide()