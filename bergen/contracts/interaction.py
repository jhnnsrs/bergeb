from bergen.console import console
from bergen.schema import Node
from bergen.graphical import GraphicalBackend


class Interaction:
    def __init__(self, node: Node) -> None:
        self.node = node

    async def graphical_assign(self):
        from bergen.ui.assignation import AssignationUI

        with console.status("[bold green]Using Graphical Assignment"):
            form = AssignationUI()
            nana = form.exec_()
        return nana


    async def __aenter__(self):
        console.log("Interaction started")
        self.graphical_backend = await GraphicalBackend().__aenter__()
        return self


    async def __aexit__(self, *args, **kwargs):
        console.log("Interaction Done")