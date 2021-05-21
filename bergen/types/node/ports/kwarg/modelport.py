

from bergen.types.node.ports.kwarg.base import BaseKwargPort
from bergen.types.node.ports.arg.base import BaseArgPort
from typing import Type
from bergen.types.node.widgets.querywidget import QueryWidget
from bergen.types.model import ArnheimModel

class ModelKwargPort(BaseKwargPort):

  def __init__(self, modelMeta, widget=None, **kwargs) -> None:
      self.modelMeta = modelMeta
      if widget is None:
        meta = self.modelMeta
        if hasattr(meta, "selector_query"):
            widget = QueryWidget(query=meta.selector_query)

        
      super().__init__(widget, **kwargs)

  def serialize(self):
      return {**super().serialize(),"identifier" : self.modelMeta.identifier}