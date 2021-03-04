#%%
from bergen.clients.default import Bergen
from bergen.models import Node
import asyncio
import time


async def main():
        async with Bergen(
                host="p-tnagerl-lab1",
                port=8000,
                client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
                client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
                name="frankomanko",# if we want to specifically only use pods on this innstance we would use that it in the selector
        ):

                sleep = await Node.asyncs.get(package="basic", interface="sodeep")
                        
                future = await sleep({"interval": 1})




if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()




# %%
