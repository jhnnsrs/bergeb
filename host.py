from pydantic import main
from bergen.messages.postman.provide import BouncedProvideMessage
from bergen.clients.actor import ActorBergen
from bergen.entertainer.actor import AsyncFuncActor
from bergen.provider.base import BaseProvider, OneExlusivePodPolicy
import asyncio
import logging
from bergen.console import console
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)




class OverWrittenAdder(AsyncFuncActor):

    async def on_provide(self):
        logger.info("Reserving")

    async def assign(self, x: int, y: int, z: int = 7) -> int:
        """Adder

        Adds x + y

        Args:
            helper ([type]): [description]
            x (int): Input X
            y (int): Input Y

        Returns:
            int: X + Y
        """
        return x + y


    async def on_unprovide(self):
        logger.info("Unreserve")


async def ainput(*args) -> str:
    with ThreadPoolExecutor(1, "AsyncInput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, console.input, *args)

async def alog(*args) -> str:
    with ThreadPoolExecutor(1, "AsyncInput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, console.log, *args)


async def main():

    async with ActorBergen(
        config_path="nana.yaml",
        force_new_token=True,
    ) as client:

        tasks = {}
        queue = asyncio.Queue()

        await asyncio.sleep(1)

        async def entertain_loop(queue):
            while True:
                message = await queue.get()
                run_task = asyncio.create_task(client.entertainer.entertain(provide, OverWrittenAdder))
                tasks[message.meta.reference] = run_task

        asyncio.create_task(entertain_loop(queue))

        while True:
            await asyncio.sleep(1)
            input = await ainput("What do you want to do? kill|start|list ")

            if input == "kill":
                indexmap = list(tasks.keys())
                number = await ainput("Which one do you want to kill?")
                task = tasks[indexmap[int(number)]]
                task.cancel()

            if input == "start":
                with open('provision.txt') as json_file:
                    data = json.load(json_file)
                    provide = BouncedProvideMessage(**data)
                    await queue.put(provide)

            if input == "list":
                console.log([f'{index}: {task}' for index, task in enumerate(tasks.keys())])



asyncio.run(main())