
from bergen.types.node.widgets.base import BaseWidget


class StringWidget(BaseWidget):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        #TODO: Inspect if widgets dependencies are okay for that query
