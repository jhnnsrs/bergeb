
from bergen.types.node.ports.base import BasePort


class IntPort(BasePort):

  def __init__(self, **kwargs) -> None:
      super().__init__("int",**kwargs)