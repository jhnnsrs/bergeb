from typing import Any
from bergen.schema import AssignationParams, Pod, PodStatus, ProvisionParams
from bergen.registries.arnheim import get_current_arnheim
import asyncio
from bergen.types.model import ArnheimModel
from bergen.extenders.base import BaseExtender
import logging
from aiostream import stream
import uuid
from bergen.extenders.contexts.pod import HostedPod



class PodExtender(BaseExtender):


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args,**kwargs)
        
        bergen = get_current_arnheim()

        self._postman = bergen.getPostman()
        self._loop, self._force_sync = bergen.getLoopAndContext()


    def unprovide(self,):
        if self._loop.is_running() and not self._force_sync:
            return self.unprovide_async()
        else:
            result = self._loop.run_until_complete(self.unprovide_async())
            return result


    # The proper functions

    async def unprovide_async(self):
        return await self._postman.unprovide(self)       

    async def assign_async(self, inputs: dict, params: AssignationParams, **kwargs):
        
        return await self._postman.assign(self, inputs, params, **kwargs)

    async def delay_async(self, inputs: dict, params: AssignationParams, **kwargs):
    
        return await self._postman.delay(self, inputs, params, **kwargs)

    def stream(self, inputs: dict, params: AssignationParams = None, **kwargs):

        return stream.iterate(self._postman.stream(self, inputs, params, **kwargs))



    # Wrappers    
    def __call__(self, inputs: dict, params: AssignationParams = None, **kwargs) -> dict:
        """Call this node (can be run both asynchronously and syncrhounsly)

        Args:
            inputs (dict): The inputs for this Node
            params (AssignationParams, optional): [description]. Defaults to None.

        Returns:
            outputs (dict): The ooutputs of this Node
        """
        if self._loop.is_running() and not self._force_sync:
            return self.assign_async(inputs, params, **kwargs)
        else:
            result = self._loop.run_until_complete(self.assign_async(inputs, params, **kwargs))
            return result


    def _repr_html_(self):
        string = f"{self.name}</br>"
        return string