
from bergen.types.node.widgets.intwidget import IntWidget
from bergen.types.node.ports.arg.base import BaseArgPort


class IntArgPort(BaseArgPort):

  def __init__(self, widget = None, **kwargs) -> None:
      if widget is None:
          widget = IntWidget()
      super().__init__("int", widget,**kwargs)