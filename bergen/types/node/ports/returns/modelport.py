

from typing import Type
from bergen.types.node.widgets.querywidget import QueryWidget
from bergen.types.node.ports.returns.base import BaseReturnPort
from bergen.types.model import ArnheimModel

class ModelReturnPort(BaseReturnPort):

  def __init__(self, modelMeta,**kwargs) -> None:
      self.modelMeta = modelMeta
      super().__init__(**kwargs)

  def serialize(self):
      return {**super().serialize(),"identifier" : self.modelMeta.identifier}