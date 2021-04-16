
from bergen.types.node.widgets import StringWidget
from bergen.types.node.ports.arg.base import BaseArgPort


class StringArgPort(BaseArgPort):

  def __init__(self, widget = None, **kwargs) -> None:
      if widget is None:
          widget = StringWidget()
      super().__init__(widget,**kwargs)