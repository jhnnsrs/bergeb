import asyncio
from contextlib import suppress

async def iterator():
    i = 0


    try:
        while True:
            await asyncio.sleep(1)
            print("Here")
            yield i
            i += 1
    except RuntimeError:
        print("Runtime")
    except asyncio.CancelledError:
        print("Cancelled")






async def main():


    message = asyncio.Queue()

    async for ev in iterator():
        if ev == 2:
            break

    print("Hallo")









if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
        print(asyncio.all_tasks())
    except Exception as e:
        print("sdfsdef", e)

    finally:
        print("Closing Loop")
        loop.close()
