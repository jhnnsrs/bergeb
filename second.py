from bergen.messages.postman.reserve.bounced_forwarded_reserve import BouncedForwardedReserveMessage
from bergen.monitor.monitor import Monitor
from platform import node
from bergen.messages.postman.unprovide import BouncedUnprovideMessage
from bergen.messages.postman.provide import BouncedProvideMessage
from bergen.clients.provider import ProviderBergen
from bergen.models import Node
from bergen.entertainer.actor import AsyncFuncActor
from bergen.provider.base import BaseProvider, OneExlusivePodPolicy
import asyncio
import logging
from bergen.console import console
import json
logger = logging.getLogger(__name__)

client = ProviderBergen(
        config_path="bergen.yaml",
        force_new_token=True,
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)

class Pfarl(AsyncFuncActor):
    
    async def on_provide(self, message):
        console.log("[red]Providing")
        return 

    async def on_reserve(self, message: BouncedForwardedReserveMessage):
        console.log("[magenta]Reserving")

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

        print(self.current_bounced)
        print(self.current_reservation_context)

        return x + y

    async def on_unreserve(self, current_reservations):
        console.log("[magenta] Unreserving")
        
        
    async def on_unprovide(self, message):
        console.log("[red]Unproviding")



@client.hook("get_actorclass_for_template", overwrite=True)
def get_actorclass_for_template(self: BaseProvider, template_id):
    return Pfarl







@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
class Schmarl(AsyncFuncActor):
    
    async def on_provide(self):
        console.log("[red]Providing")

    async def on_reserve(self, message: BouncedForwardedReserveMessage):
        console.log("[magenta]Reserving")

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

        print(self.current_bounced)
        print(self.)

        return x + y

    async def on_unreserve(self, current_reservations):
        console.log("[magenta] Unreserving")
        
        
    async def on_unprovide(self):
        console.log("[red]Unproviding")



@client.provider.enable(gpu=True, policy=OneExlusivePodPolicy())
class Karl(AsyncFuncActor):
    
    async def on_provide(self):
        self.node1 = await Node.asyncs.get(package="Flow Boy", interface="newadder")

    async def on_reserve(self, message: BouncedForwardedReserveMessage):
        return {
            "FlowBoy" : await self.node1.reserve(room="sted", auto_provide=True, auto_unprovide=True, bounced=message.meta.token).start()
        }


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

        print(self.node1)
        print(self.current_bounced)
        print(self.current_reservations)


        return await self.current_reservations["FlowBoy"].assign(x, y)

    async def on_unreserve(self, current_reservations):
        for key, reservation in current_reservations.items():
            console.log(f"[yellow]Cancelling {key}")
            await reservation.end()
        
        
    async def on_unprovide(self):
        logger.info("Unreserve")




client.provide()