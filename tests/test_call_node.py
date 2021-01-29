from bergen.enums import ClientType, GrantType
from bergen.clients.default import Bergen
from bergen.models import Node, Template
import pytest
import asyncio


def test_node_assign():

    liner = Node.objects.get(package="@canoncial/generic/filters", interface="sleep")
    rep = liner({"rep": 1})
    assert isinstance(rep, dict), "Received weird error"


@pytest.fixture(scope='session')
def loop():
    return asyncio.get_event_loop()


async def test_async(loop):
    
    client = Bergen(host="p-tnagerl-lab1",
                client_id= "EEjI4z8Gahr6TU6dujnq2Q6pAojcit3iCILF9Ggm",
                client_secret= "Onbmcglhf18rXi0D1pvfeCwnuIGZZV8xpbktzdFXaMs5zpIFG5NJRR2R7pS7RlCgZ6bfiId317XUIrQ1EudJye2WNpZ5jjvbQWul4nyuEECNestHCIUEPCBb3B8DmdwV",
                port=8000,
                name="karl",
                username = "stephane",
                password = "bancelin12345",
                loop=loop,
                client_type=ClientType.EXTERNAL,
                grant_type=GrantType.PASSWORD
    )

    sleep = await Node.asyncs.get(package="@canoncial/generic/filters", interface="sleep")
    result = await sleep({"rep": 1})
    
