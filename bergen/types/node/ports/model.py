

from bergen.types.node.ports.base import BasePort
from bergen.types.model import ArnheimModel

class ModelPort(BasePort):

  def __init__(self, modelClass: ArnheimModel, **kwargs) -> None:
      self.modelClass = modelClass
      super().__init__("model",**kwargs)

  def serialize(self):
      return {**super().serialize(),"identifier" : self.modelClass.getMeta().identifier}