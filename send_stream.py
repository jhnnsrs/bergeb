#%%
from bergen.clients.default import Bergen
from bergen.models import Node
import asyncio
import time

Bergen(
                host="p-tnagerl-lab1",
                port=8000,
                client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
                client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
                name="frankomanko",
                jupyter=True,
                force_sync=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)

#%%
sleep = Node.objects.get(package="basic", interface="sleep")

#%%
sleep({"interval": 1}, with_progress=True)




# %%
