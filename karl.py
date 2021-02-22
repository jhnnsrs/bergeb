
from bergen.clients.host import HostBergen
from bergen.models import Node, Pod
import asyncio
import time


client = HostBergen(
        host="p-tnagerl-lab1",
        port=8000,
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        name="franz",
        force_sync=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)


sleep = Node.objects.get(package="basic", interface="sleep")


@client.register(sleep, gpu=True)
async def sleep(helper, interval=1):
    print("Was called")
    for i in range(0,1):
        print(f"Sleeping for {interval}")
        await asyncio.sleep(interval)
    return {"interval": interval}


client.run()
