
from bergen.clients.host import HostBergen
from bergen.models import Node
import asyncio
import time

client = HostBergen(
        host="localhost",
        port=8000,
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        name="karl",
        force_sync=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)


sleep = Node.objects.get(package="basic", interface="sleep")

@client.register(sleep, gpu=True)
async def sleep(helper, interval=1):
    print("Was called")
    for i in range(0,1):
        await helper.progress(f"Sleeeping...{interval}",percentage=i*10)
        await asyncio.sleep(interval)
        yield {"interval": interval}


client.run()
