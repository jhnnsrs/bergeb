import asyncio
from typing import Any
from bergen.contracts.reservation import Reservation
from bergen.contracts.interaction import Interaction

from bergen.monitor.monitor import Monitor
from bergen.messages.postman.reserve.bounced_reserve import ReserveParams
from bergen.schema import AssignationParams, Node
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
        
        bergen = get_current_client()

        self._postman = bergen.getPostman()
        self._loop = bergen.loop


    def interactive(self) -> Interaction:
        return Interaction(self)

    def reserve(self, loop=None, monitor: Monitor = None, ignore_node_exceptions=False, bounced=None, **params) -> Reservation:
        return Reservation(self, loop=loop, monitor=monitor, ignore_node_exceptions=ignore_node_exceptions, bounced=bounced, **params)

    async def stream(self, inputs: dict, params: ReserveParams = None, **kwargs):
        return stream.iterate(self._postman.stream(self, inputs, params, **kwargs))

    def _repr_html_(self: Node):
        string = f"{self.name}</br>"

        for arg in self.args:
            string += "Args </br>"
            string += f"Port: {arg._repr_html_()} </br>"

        for kwarg in self.kwargs:
            string += "Kwargs </br>"
            string += f"Port: {kwarg._repr_html_()} </br>"


        return string


    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return super().__call__(*args, **kwds)


    def __rich__(self):
        my_table = Table(title=f"Node: {self.name}", show_header=False)

        my_table.add_row("ID", str(self.id))
        my_table.add_row("Package", self.package)
        my_table.add_row("Interface", self.interface)

        return my_table