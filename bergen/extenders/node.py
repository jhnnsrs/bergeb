from typing import Any
from bergen.schema import AssignationParams, Template
from bergen.wards.graphql.subscription import SubscriptionGraphQLWard
from bergen.registries.arnheim import get_current_arnheim
import asyncio
from bergen.types.model import ArnheimModel
from bergen.extenders.base import BaseExtender
import logging
from aiostream import stream
import uuid



logger = logging.getLogger(__name__)



def serialize(inputs: dict):
    serialized_inputs = {}
    
    for key, value in inputs.items():
        if isinstance(value, ArnheimModel):
            serialized_inputs[key] = value.id
        else:
            serialized_inputs[key] = value

    return serialized_inputs


class AsyncPodHandler:

    def __init__(self, provisionHandler, ward, node, pod) -> None:
        self._pod = pod
        self._node = node
        self._provisionHandler = provisionHandler
        self._ward = ward
        super().__init__()


    async def stream(self, inputs: dict):
        from arnheim.constants import ASSIGN_GQL
        logger.info(f"Trying to assign to {self._pod}")
        serialized_inputs = {}

        serialized_inputs = serialize(inputs)

        expandedoutputs = None
        async for item in ASSIGN_GQL.subscribe(self._ward, variables={"pod": self._pod.id, "inputs": serialized_inputs, "reference": str(uuid.uuid4())}):
            if item.status == "DONE":
                from arnheim.utils import expandOutputs
                expandedoutputs = expandOutputs(self._node, item.outputs)
                yield expandedoutputs
                break
            elif item.status == "YIELD":
                from arnheim.utils import expandOutputs
                expandedoutputs = expandOutputs(self._node, item.outputs)
                yield expandedoutputs
            elif item.status == "CRITICAL":
                raise Exception(item.statusmessage)
            else:
                pass


    async def assign(self, inputs: dict):
        from arnheim.constants import ASSIGN_GQL
        logger.debug(f"Trying to assign to {self._pod}")
        serialized_inputs = {}

        serialized_inputs = serialize(inputs)

        async for item in ASSIGN_GQL.subscribe(self._ward, variables={"pod": self._pod.id, "inputs": serialized_inputs, "reference": str(uuid.uuid4())}):
            logger.info(f"Received {item}")
            if item.status == "DONE":
                from arnheim.utils import expandOutputs
                expandedoutputs = expandOutputs(self._node, item.outputs)
                return expandedoutputs
            elif item.status == "CRITICAL":
                raise Exception(item.statusmessage)
            else:
                pass


    async def kill(self):
        await asyncio.sleep(0.01)
        logger.info("Closed Connection")


class ProvisionHandler:

    def __init__(self, nodeModel, ward: SubscriptionGraphQLWard, template: Template = None) -> None:
        super().__init__()
        self._pod = None
        self._ward = ward
        self._template = template
        self._node = nodeModel

    async def __aenter__(self):
        from bergen.constants import PROVIDE_GQL

        async for item in PROVIDE_GQL.subscribe(self._ward, variables={"node": self._node.id, "selector": {"template": self.template.id, "kwargs": {"volunteer": 2}}, "reference": str(uuid.uuid4())}):
            if item.pod.status == "ACTIVE":
                self._provisionreference = item.reference 
                self._pod = AsyncPodHandler(self, self._ward, self._node, item.pod)
                return self._pod
            else:
                pass

    


    async def assign(self, inputs):
        async with self as handler:
            return await handler.assign(inputs)

        
    async def __aexit__(self, exc_type, exc, tb):
        await self._pod.kill()
        print(exc_type, exc, tb)
        self._pod = None





class NodeExtender(BaseExtender):


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args,**kwargs)
        
        self._postman = get_current_arnheim().getPostman()

    async def __call_async(self, inputs: dict, params: AssignationParams, **kwargs):
        
        return await self._postman.assign(self, inputs, params, **kwargs)

    async def __delay_async(self, inputs: dict, params: AssignationParams, **kwargs):
    
        return await self._postman.delay(self, inputs, params, **kwargs)

    async def stream(self, inputs: dict, template: Template):

        return stream.count(interval=0.2)
    
    def delay(self, inputs: dict, params: AssignationParams = None, **kwargs):
        try:
            event_loop = asyncio.get_event_loop()
        except RuntimeError:
            pass
        else:
            if event_loop.is_running():
                return self.__delay_async(inputs, params, **kwargs)
            else:
                logger.info("Spinning up new eventloop just for that <3")
                event_loop = asyncio.get_event_loop()
                result = event_loop.run_until_complete(self.__delay_async(inputs, params, **kwargs))
                return result



    def __call__(self, inputs: dict, params: AssignationParams = None, **kwargs) -> dict:
        """Call this node (can be run both asynchronously and syncrhounsly)

        Args:
            inputs (dict): The inputs for this Node
            params (AssignationParams, optional): [description]. Defaults to None.

        Returns:
            outputs (dict): The ooutputs of this Node
        """
        try:
            event_loop = asyncio.get_event_loop()
        except RuntimeError:
            pass
        else:
            if event_loop.is_running():
                return self.__call_async(inputs, params, **kwargs)
            else:
                logger.info("Spinning up new eventloop just for that <3")
                event_loop = asyncio.get_event_loop()
                result = event_loop.run_until_complete(self.__call_async(inputs, params, **kwargs))
                return result

    def provide(self, provider = "vart"):

        ward = get_current_arnheim().getWard()
        self._provisionhandler = ProvisionHandler(self, ward, provider=provider)
        return self._provisionhandler


    def _repr_html_(self):
        string = f"{self.name}</br>"

        for input in self.inputs:
            string += "Inputs </br>"
            string += f"Port: {input._repr_html_()} </br>"

        for output in self.outputs:
            string += "Outputs </br>"
            string += f"Port: {output._repr_html_()} </br>"


        return string