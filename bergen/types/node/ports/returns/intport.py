
from bergen.types.node.widgets.intwidget import IntWidget
from bergen.types.node.ports.returns.base import BaseReturnPort


class IntReturnPort(BaseReturnPort):

  def __init__(self, **kwargs) -> None:
      super().__init__(**kwargs)