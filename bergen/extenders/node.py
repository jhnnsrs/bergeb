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

    def __init__(self, nodeModel, ward: SubscriptionGraphQLWard, provider="vart") -> None:
        super().__init__()
        self._pod = None
        self._ward = ward
        self._provider = provider
        self._node = nodeModel

    async def __aenter__(self):
        from arnheim.constants import PROVIDE_GQL

        async for item in PROVIDE_GQL.subscribe(self._ward, variables={"node": self._node.id, "selector": {"provider": self._provider, "kwargs": {"volunteer": 2}}, "reference": str(uuid.uuid4())}):
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
        self._pod = "Hallo"

    def __call__as_stream(self, inputs, provider):
        logger.info(f"Called as Stream")
        return stream.count(interval=0.2)

    async def __call_async(self, inputs, provider):
        
        async with self.provide(provider=provider) as handler:
            return await handler.assign(inputs=inputs)

    async def __await_call_async(self, inputs,provider):
        return await self.__call_async(inputs, provider)

    def __call_sync(self, inputs, provider):
        logger.info(f"Called in Sync")
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.__await_call_async(inputs, provider))
        loop.close()
        return result

    def __call__(self, inputs: dict, provider="vart", stream=False):
        """Call this method to notify all subscriptions in the group.
        This method can be called from both synchronous and asynchronous
        contexts. If you call it from the asynchronous context then you
        have to `await`.
        Args:
            group: Name of the subscription group which members must be
                notified. `None` means that all the subscriptions of
                type will be triggered.
            payload: The payload delivered to the `publish` handler.
                NOTE: The `payload` is serialized before sending
                to the subscription group.
        """
        try:
            event_loop = asyncio.get_event_loop()
        except RuntimeError:
            pass
        else:
            if event_loop.is_running():
                if stream: return self.__call__as_stream(inputs, provider)
                return self.__call_async(inputs, provider)
        

            
        return self.__call_sync(inputs, provider)

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