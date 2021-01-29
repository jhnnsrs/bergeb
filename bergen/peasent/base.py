

from abc import ABC, abstractmethod
from typing import Union
from bergen.utils import ExpansionError, expandInputs
from bergen.messages.assignation import AssignationMessage
from bergen.schema import Template
from bergen.constants import OFFER_GQL, SERVE_GQL
import logging
import namegenerator
import asyncio
import websockets
from bergen.models import Node
import inspect
import sys

logger = logging.getLogger()

import json

class BasePeasent(ABC):
    ''' Is a mixin for Our Bergen '''


    def __init__(self, *args, loop = None, unique_name = None, **kwargs) -> None:
        
        
        self.unique_name = unique_name or namegenerator.gen()
        self.loop = loop or asyncio.get_event_loop()
        self.pods = {}

        self.templates_to_register = []
        self.pods_to_register = []
        super().__init__(*args, loop=loop, **kwargs)


    def register(self, node_or_template: Union[Node, Template], **kwargs):


        def real_decorator(function):

            async def wrapper(message: AssignationMessage):
                helper = {}

                kwargs = message.data.inputs
                
                if inspect.iscoroutinefunction(function):
                    result = await function(helper, **kwargs)

                    return result
                else:
                    raise NotImplementedError("We do not allow for non async functions right now")
                
            
            wrapper.__name__ = function.__name__

            if isinstance(node_or_template, Node):
                logger.info(f"Registering Template for {node_or_template.name}")
                self.templates_to_register.append({
                    "node": node_or_template,
                    "params": kwargs,
                    "function": wrapper

                })

            if isinstance(node_or_template, Template):
                logger.info(f"Registering Potential Pod for {node_or_template.id}")
                self.pods_to_register.append({
                    "template": node_or_template,
                    "function": wrapper


                })


            return wrapper


        return real_decorator



    async def setup_and_run(self):
        self.peasent = await SERVE_GQL.run_async(ward=self.main_ward, variables = {"name":self.unique_name})
        
        async def offer(node: Node, params: dict, function):
            peasent_template = await OFFER_GQL.run_async(ward=self.main_ward, variables= {"node": node.id, "params": params, "peasent": self.peasent.id})
            return (peasent_template, function)

        template_function_set = await asyncio.gather(*[offer(**values) for values in self.templates_to_register])
        self.templateid_function_map = {value[0].id: value[1] for value in template_function_set}
        self.templateid_template_map = {value[0].id: value[0] for value in template_function_set}

        print(self.templateid_function_map)

        await self.configure()





    @abstractmethod
    async def configure(self) -> str:


        raise NotImplementedError("Please overwrite")


    def run(self):

        self.loop.create_task(self.setup_and_run())

        # we enter a never-ending loop that waits for data
        # and runs callbacks whenever necessary.
        
        self.loop.run_forever()

