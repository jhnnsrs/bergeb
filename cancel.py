#%%
from bergen.clients.default import Bergen
from bergen.models import Node
from bergen.monitor.monitor import Monitor
import asyncio
import time


async def main():
        async with Bergen(config_path="tests/configs/implicit.yaml", force_new_token=True):
            zseries = await Node.asyncs.get(package="Flow Boy", interface="newadder")

            with Monitor(title="testing", progress=True):
                async with zseries.reserve(room="sted", auto_provide=True, auto_unprovide=False) as res:
                    future = asyncio.ensure_future(res.assign(100,200,z=0))

                    await asyncio.sleep(1)
                    if not future.cancelled():
                        future.cancel()
                    else:
                        my_task = None

                    await asyncio.sleep(2)
                    try:
                        await future.result()
                    except:
                        pass




if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()




# %%
