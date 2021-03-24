

from bergen.types.node.ports.kwarg.base import BaseKwargPort
from bergen.types.node.ports.arg.base import BaseArgPort
from typing import Type
from bergen.types.node.widgets.querywidget import QueryWidget
from bergen.types.model import ArnheimModel

class ModelKwargPort(BaseKwargPort):

  def __init__(self, modelClass: Type[ArnheimModel], widget=None, **kwargs) -> None:
      self.modelClass = modelClass
      if widget is None:
        meta = self.modelClass.getMeta()
        if hasattr(meta, "selector_query"):
            widget = QueryWidget(query=meta.selector_query)

      assert widget is not None, "You didn't provide a widget nor has it been declared in the meta class of the Model"
        
      super().__init__("model", widget, **kwargs)

  def serialize(self):
      return {**super().serialize(),"identifier" : self.modelClass.getMeta().identifier}