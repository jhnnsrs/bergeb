
from bergen.types.node.widgets.base import BaseWidget


class IntWidget(BaseWidget):

    def __init__(self, min=None, max=None, **kwargs) -> None:
        super().__init__("int", **kwargs)
        self.min = min
        self.max = max
        #TODO: Inspect if widgets dependencies are okay for that query

    def params(self):
        return { "min": self.min, "max": self.max}