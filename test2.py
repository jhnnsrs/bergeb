from bergen.enums import ClientType
from bergen.clients.default import Bergen
from bergen.models import Node
import asyncio
import time




async def main(loop):

    client = Bergen(
        host="p-tnagerl-lab1",
        port=8000,
        client_id="OyTXRTXNLu6HQpegcch94eQScyrEC85tH0OkstKO", 
        client_secret="nhSPWLVe1Ub2UOEc231KL0KmCQkIpPGubcqJr176wYfSLgLshmJChPmAi7RPs7i1KifjyOmNrPild8VGvkUWfPkvy7dBWfgUPPo6QBTHSTjZluLngrCLg6NiVEF9hbgB",
        name="karl",
        loop=loop,
        client_type=ClientType.INTERNAL
    )

    sleep = await Node.asyncs.get(package="@canoncial/generic/filters", interface="sleep")


    start = time.time()
    output = await asyncio.gather(*[sleep({"rep": 1}) for i in range(0,1000)])

    print(output)
    print( time.time() - start)




if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()