
from bergen.types.node.widgets.intwidget import IntWidget
from bergen.types.node.ports.outs.base import BaseOutPort


class IntOutPort(BaseOutPort):

  def __init__(self, **kwargs) -> None:
      super().__init__("int",**kwargs)