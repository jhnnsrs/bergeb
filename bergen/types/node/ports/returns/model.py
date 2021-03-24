

from typing import Type
from bergen.types.node.widgets.querywidget import QueryWidget
from bergen.types.node.ports.returns.base import BaseReturnPort
from bergen.types.model import ArnheimModel

class ModelReturnPort(BaseReturnPort):

  def __init__(self, modelClass: Type[ArnheimModel],**kwargs) -> None:
      self.modelClass = modelClass
      super().__init__("model", **kwargs)

  def serialize(self):
      return {**super().serialize(),"identifier" : self.modelClass.getMeta().identifier}