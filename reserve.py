from pydantic.utils import truncate
from bergen.types.node.widgets.querywidget import QueryWidget
from bergen.schema import ArnheimApplication
from bergen.clients.host import Bergen
from bergen.models import Node
from typing import Type, TypedDict
import asyncio


async def main():

    async with Bergen(name="karl"):
        zeries = await Node.asyncs.get(package="sasa", interface="assign")

        await zeries.provide().provide()

        async with zeries.reserve(room="sted", on_progress= lambda x: print(x)) as res:
            lala = await asyncio.gather(*[res.assign(100,200,z=0) for i in range(1000)])
            print(lala)

        print(zeries)


            


if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()