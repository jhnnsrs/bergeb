

from bergen.types.node.ports.arg.base import BaseArgPort
from typing import Type
from bergen.types.node.widgets import QueryWidget
from bergen.types.model import ArnheimModel

class ModelArgPort(BaseArgPort):

  def __init__(self, modelMeta, widget=None, **kwargs) -> None:
      self.modelMeta = modelMeta
      if widget is None:
        if hasattr(self.modelMeta, "selector_query"):
            widget = QueryWidget(query=self.modelMeta.selector_query)

        
      super().__init__(widget, **kwargs)

  def serialize(self):
      return {**super().serialize(),"identifier" : self.modelMeta.identifier}