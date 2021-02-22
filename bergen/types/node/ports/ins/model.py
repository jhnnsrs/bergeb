

from typing import Type
from bergen.types.node.widgets.querywidget import QueryWidget
from bergen.types.node.ports.ins.base import BaseInPort
from bergen.types.model import ArnheimModel

class ModelInPort(BaseInPort):

  def __init__(self, modelClass: Type[ArnheimModel], widget=None, **kwargs) -> None:
      self.modelClass = modelClass
      if widget is None:
        meta = self.modelClass.getMeta()
        try:
            selector = meta.selector_query
            widget = QueryWidget(query=selector)
        except:
            raise Exception("You didn't provide a widget nor has it been declared in the meta class of the Model")
        
      super().__init__("model", widget, **kwargs)

  def serialize(self):
      return {**super().serialize(),"identifier" : self.modelClass.getMeta().identifier}