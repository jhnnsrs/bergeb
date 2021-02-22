
from typing import Any
from bergen.schema import AssignationParams, Pod, PodStatus, ProvisionParams
from bergen.registries.arnheim import get_current_arnheim
from bergen.types.model import ArnheimModel
from bergen.extenders.base import BaseExtender
from aiostream import stream
from bergen.extenders.contexts.pod import HostedPod
from tqdm import tqdm
import textwrap



class AssignationUIMixin:

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._ui = None


    def askInputs(self, **kwargs) -> dict:
        widget = self.getWidget(**kwargs) # We have established a ui
        if widget.exec_():
            return widget.parameters
        else:
            return None


    def getWidget(self, **kwargs):
        try:
            from bergen.ui.assignation import AssignationUI
            if not self._ui:
                self._ui = AssignationUI(self.inputs, **kwargs)
            return self._ui
        except ImportError as e:
            raise NotImplementedError("Please install PyQt5 in order to use interactive Widget based parameter query")
            
        





class NodeExtender(AssignationUIMixin, BaseExtender):


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args,**kwargs)
        
        bergen = get_current_arnheim()

        self._postman = bergen.getPostman()
        self._loop, self._force_sync = bergen.getLoopAndContext()


    def provide(self, params: ProvisionParams, **kwargs):
        if self._loop.is_running() and not self._force_sync:
            return self.provide_async(params, **kwargs)
        else:
            result = self._loop.run_until_complete(self.provide_async(params, **kwargs))
            return result

    async def provide_async(self, params: ProvisionParams, **kwargs):
        return await self._postman.provide(self, params, **kwargs)       

    async def assign_async(self, inputs: dict, params: AssignationParams, **kwargs):
        
        return await self._postman.assign(self, inputs, params, **kwargs)

    async def delay_async(self, inputs: dict, params: AssignationParams, **kwargs):
    
        return await self._postman.delay(self, inputs, params, **kwargs)

    def stream(self, inputs: dict, params: AssignationParams = None, **kwargs):

        return stream.iterate(self._postman.stream(self, inputs, params, **kwargs))


    async def assign_with_progress(self, inputs, params, **kwargs):
        result = None
        with tqdm(total=100) as pbar:
                async with self.stream_progress(inputs, params, **kwargs) as stream:
                        async for item in stream:
                                result = item
                                if isinstance(result, dict): break
                                
                                progress, message = item.split(":")
                                try: 
                                        pbar.n = int(progress)
                                        pbar.refresh()
                                except:
                                        pass
                                pbar.set_postfix_str(textwrap.shorten(message, width=30, placeholder="..."))
                pbar.n = 100
                pbar.refresh()
                pbar.set_postfix_str("Done")
        return result


    def stream_progress(self,  inputs: dict, params: AssignationParams = None, **kwargs):
        return stream.iterate(self._postman.stream_progress(self, inputs, params, **kwargs)).stream()
    
    def delay(self, inputs: dict, params: AssignationParams = None, **kwargs):
        if self._loop.is_running() and not self._force_sync:
            return self.delay_async(inputs, params, **kwargs)
        else:
            result = self._loop.run_until_complete(self.delay_async(inputs, params, **kwargs))
            return result


    def __call__(self, inputs: dict, params: AssignationParams = None, with_progress = False, **kwargs) -> dict:
        """Call this node (can be run both asynchronously and syncrhounsly)

        Args:
            inputs (dict): The inputs for this Node
            params (AssignationParams, optional): [description]. Defaults to None.

        Returns:
            outputs (dict): The ooutputs of this Node
        """
    
        if self._loop.is_running() and not self._force_sync:
            if with_progress == True:
                return self.assign_with_progress(inputs, params,  with_progress=with_progress, **kwargs)
            return self.assign_async(inputs, params, with_progress=with_progress, **kwargs)

        else:
            if with_progress == True:
                return self._loop.run_until_complete(self.assign_with_progress(inputs, params,  with_progress=with_progress, **kwargs))

            result = self._loop.run_until_complete(self.assign_async(inputs, params,  with_progress=with_progress, **kwargs))
            return result



    def hosted(self, params: ProvisionParams = {}, enter_when = PodStatus.ACTIVE, **kwargs):
        return HostedPod(self, params = {}, enter_when=enter_when, **kwargs)

    def _repr_html_(self):
        string = f"{self.name}</br>"

        for input in self.inputs:
            string += "Inputs </br>"
            string += f"Port: {input._repr_html_()} </br>"

        for output in self.outputs:
            string += "Outputs </br>"
            string += f"Port: {output._repr_html_()} </br>"


        return string