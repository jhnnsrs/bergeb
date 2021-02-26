from bergen.types.node.widgets.querywidget import QueryWidget
from bergen.schema import ArnheimApplication
from bergen.clients.host import HostBergen
from bergen.models import Node
import asyncio
import time
from typing import Type, TypedDict



client = HostBergen(
        host="p-tnagerl-lab1",
        port=8090,
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        name="karl",
        force_sync=True,
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)


@client.enable(gpu=True, 
                widgets={
                    "rep": QueryWidget("""
                            query {
                                data: myrepresentations {
                                    value: id
                                    label: name
                            }
                            """)

})
async def friend(helper, rep: ArnheimApplication = None, interval: int = 5) -> TypedDict("",rep=ArnheimApplication):
    """Friend

    Friend is a motherfucker that enables everything you could ever wish for

    Args:
        rep ([type], optional): Ohhh boy you would like to know. Defaults to None.

    Returns:
        [type]: [description]
    """

    return {"rep": 1}



client.run()