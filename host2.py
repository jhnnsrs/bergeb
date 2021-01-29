from bergen.peasent.websocket import WebsocketPeasent
from bergen.peasent.pika import PikaPeasent
from bergen.clients.default import Bergen
from bergen.models import Node
import asyncio

class HostBergen(WebsocketPeasent, Bergen):
    pass


client = HostBergen(
        host="p-tnagerl-lab1",
        port=8000,
        client_id="OyTXRTXNLu6HQpegcch94eQScyrEC85tH0OkstKO", 
        client_secret="nhSPWLVe1Ub2UOEc231KL0KmCQkIpPGubcqJr176wYfSLgLshmJChPmAi7RPs7i1KifjyOmNrPild8VGvkUWfPkvy7dBWfgUPPo6QBTHSTjZluLngrCLg6NiVEF9hbgB",
        unique_name="image_g",# if we want to specifically only use pods on this innstance we would use that it in the selector
)


sleep = Node.objects.get(package="@canoncial/generic/filters", interface="sleep")
prewitt = Node.objects.get(package="@canoncial/generic/filters", interface="prewitt")



@client.register(sleep, gpu=True)
async def sleep(helper, rep=None):
    """Sleeps on the GPU 

    Args:
        helper ([type]): [description]
        rep ([type], optional): [description]. Defaults to None.
    """
    await asyncio.sleep(0.2)
    return {"rep" : 1}

@client.register(prewitt, gpu=True)
async def prewitt(helper, rep=None):
    """Sleep on the CPU

    Args:
        helper ([type]): [description]
        rep ([type], optional): [description]. Defaults to None.
    """
    await asyncio.sleep(0.2)
    return {"rep" : 1}


client.run()