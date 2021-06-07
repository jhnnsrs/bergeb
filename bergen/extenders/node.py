import asyncio
from bergen.legacy.utils import get_running_loop
from typing import Any
from bergen.contracts.reservation import Reservation
from bergen.contracts.interaction import Interaction

from bergen.monitor.monitor import Monitor
from bergen.messages.postman.reserve.bounced_reserve import ReserveParams
from bergen.schema import AssignationParams, Node, NodeType
from bergen.registries.client import get_current_client
from bergen.contracts import Reservation
from aiostream import stream
from tqdm import tqdm
import textwrap
import logging
from rich.table import Table
from rich.table import Table


logger = logging.getLogger(__name__)

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



class NodeExtender(AssignationUIMixin):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args,**kwargs)
        
        client = get_current_client()

        self._postman = client.postman
        self._loop = client.loop


    def interactive(self) -> Interaction:
        return Interaction(self)

    def reserve(self, loop=None, monitor: Monitor = None, ignore_node_exceptions=False, bounced=None, **params) -> Reservation:
        return Reservation(self, loop=loop, monitor=monitor, ignore_node_exceptions=ignore_node_exceptions, bounced=bounced, **params)

   

    def _repr_html_(self: Node):
        string = f"{self.name}</br>"

        for arg in self.args:
            string += "Args </br>"
            string += f"Port: {arg._repr_html_()} </br>"

        for kwarg in self.kwargs:
            string += "Kwargs </br>"
            string += f"Port: {kwarg._repr_html_()} </br>"


        return string


    async def assign(self, *args, reserve_params: dict = {}, **kwargs):
        async with self.reserve(**reserve_params) as res:
            return await res.assign(*args, **kwargs)

    async def stream(self, *args, reserve_params: dict = {}, **kwargs):
        async with self.reserve(**reserve_params) as res:
            async for result in res.stream(*args, **kwargs):
                yield result

        


    def __call__(self, *args: Any,  reserve_params: ReserveParams = None, **kwargs) -> Any:
        try:
            loop = get_running_loop()
        except RuntimeError:
            assert self.type == NodeType.FUNCTION, "Can only call node functions syncronoicouly"
            self._loop.run_until_complete()
        else:
            if self.type == NodeType.GENERATOR:
                return self.stream(*args, **kwargs)
            if self.type == NodeType.FUNCTION:
                return self.assign(*args, **kwargs)


    def __rich__(self):
        my_table = Table(title=f"Node: {self.name}", show_header=False)

        my_table.add_row("ID", str(self.id))
        my_table.add_row("Package", self.package)
        my_table.add_row("Interface", self.interface)
        my_table.add_row("Type", self.type)

        return my_table