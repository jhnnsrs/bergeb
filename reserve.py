from bergen.monitor.monitor import Monitor
from bergen.clients.host import Bergen
from bergen.models import Node
import asyncio


async def use(package=None, interface=None) -> Node:
    return await Node.asyncs.get(package=package, interface=interface)



async def stream(res, *args, **kwargs):
        async for value in res.stream(*args, **kwargs):
            print("nana", str(value))

        print("Done")

async def assign(node, *args, **kwargs):
        async with node.reserve(room="sted", auto_provide=True, auto_unprovide=False) as res:
            return await res.assign(*args, **kwargs)




async def app_assign():

    async with Bergen(config_path="client.yaml", force_new_token=True):

        adder = await use(package="Test Implicit", interface="adder")

        with Monitor(title="testing", log=True):
            async with adder.reserve(auto_provide=True, auto_unprovide=False) as res:
                result = await res.assign(4,3)
                print(result)



async def app_stream():

    async with Bergen(config_path="client.yaml", log_stream=True, force_new_token=True):

        yielder = await use(package="Test Implicit", interface="intyielder")
        adder = await use(package="Test Implicit", interface="adder")


        async def iterate():
            async for result in yielder(interval=2):
                print(result)

        with Monitor(title="testing", log=True):
            nana = asyncio.create_task(iterate())
            await asyncio.sleep(5)

            nana.cancel()
            print("Cancelled Called")
            await nana


            print("Hallo")


            


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app_stream())