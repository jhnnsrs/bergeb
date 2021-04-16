
from bergen.types.node.widgets import StringWidget
from bergen.types.node.ports.kwarg.base import BaseKwargPort


class StringKwargPort(BaseKwargPort):

  def __init__(self, widget = None, **kwargs) -> None:
      if widget is None:
          widget = StringWidget()
      super().__init__(widget,**kwargs)