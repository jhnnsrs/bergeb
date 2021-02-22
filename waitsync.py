
from bergen.peasent.base import AssignationHelper
from bergen.clients.host import HostBergen
from bergen.models import Node
import asyncio
import time

client = HostBergen(
        host="p-tnagerl-lab1",
        port=8000,
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        name="schwankolanko",# if we want to specifically only use pods on this innstance we would use that it in the selector
)


sleep = Node.objects.get(package="basic", interface="sleep")

@client.register(sleep, gpu=True)
def sleep(helper: AssignationHelper, interval=1):
    helper.progress( "Started", percentage=10)
    time.sleep(5)
    helper.progress("Going high", percentage=20)
    time.sleep(1)
    helper.progress("Gotta love sleeping", percentage=30)
    time.sleep(3)
    helper.progress("Not ready yet", percentage=40)
    time.sleep(1)
    helper.progress("yesyes", percentage=80)
    time.sleep(4)
    return {"interval": 1}


client.run()
