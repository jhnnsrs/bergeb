#%%
from bergen.clients.default import Bergen
from bergen.models import Node
import asyncio
import time

client = Bergen(
                host="p-tnagerl-lab1",
                port=8000,
                client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
                client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu", 
                jupyter=True,
                force_sync=True            
)

# %%
nana = Node.objects.get(package="basic", interface="sleep")
# %%
nana
# %%
