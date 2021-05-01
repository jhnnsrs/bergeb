from bergen.monitor.monitor import Monitor
from bergen.clients.host import Bergen
from bergen.models import Node
import asyncio


async def use(package=None, interface=None) -> Node:
    return await Node.asyncs.get(package=package, interface=interface)


async def stream(node, *args, **kwargs):
    with Monitor(title="testing"):
        async with node.reserve(room="sted", auto_provide=True, auto_unprovide=False) as res:
            async for value in res.stream(*args, **kwargs):
                res.log("nana", str(value))

            print("Done")

async def assign(node, *args, **kwargs):
    with Monitor(title="testing"):
        async with node.reserve(room="sted", auto_provide=True, auto_unprovide=False) as res:
            return await res.assign(*args, **kwargs)




async def main():

    async with Bergen(config_path="tests/configs/implicit.yaml", force_new_token=True):

        zeries = await use(package="Fluss", interface="Image Analysis")

        async for result in zeries.assign(x = 4, y = 6):
            print(result)
            




            


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()