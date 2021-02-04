from bergen.enums import ClientType, GrantType
from bergen.clients.default import Bergen
from bergen.models import Node, Template
import pytest
import asyncio


def test_node_assign():

    client = Bergen(host="p-tnagerl-lab1",
        port=8000,
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        name="karl",# if we want to specifically only use pods on this innstance we would use that it in the selector
    )


    sleep = Node.objects.get(package="basic", interface="sleep")
    rep = sleep({"interval": 1})
    assert isinstance(rep, dict), "Received weird error"
    assert isinstance(rep["interval"], int), "Return didn't adhere to sleep paradigm"


@pytest.fixture(scope='session')
def loop():
    return asyncio.get_event_loop()


async def test_async(loop):
    
    async with Bergen(host="p-tnagerl-lab1",
        port=8000,
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        name="karl",# if we want to specifically only use pods on this innstance we would use that it in the selector
        ):  
    
        sleep = await Node.asyncs.get(package="basic", interface="sleep")
        result = await sleep({"interval": 1})