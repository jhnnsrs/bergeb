from bergen.clients.default import Bergen
from bergen.models import Node, Template
import pytest
import asyncio
import os

TEST_PACKAGE = "ImageJ"
TEST_NODE = "newadder"

folder_path = os.path.dirname(os.path.abspath(__file__))
print(folder_path)


def test_node_assign():

    client = Bergen(config_path=os.path.join(folder_path, "configs/backend.yaml"), force_new_token=True)
    sleep = Node.objects.get(package=TEST_PACKAGE, interface=TEST_NODE)


@pytest.fixture(scope='session')
def loop():
    return asyncio.get_event_loop()


async def test_async(loop):
    
    async with Bergen(config_path=os.path.join(folder_path, "configs/backend.yaml"), force_new_token=True):  
    
        sleep = await Node.asyncs.get(package=TEST_PACKAGE, interface=TEST_NODE)