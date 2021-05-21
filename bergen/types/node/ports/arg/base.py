import inspect
from typing import DefaultDict
from bergen.types.node.widgets.base import BaseWidget


class BaseArgPort:

  def __init__(self, widget, key=None, label=None, description=None) -> None:
      assert isinstance(widget, BaseWidget) or widget is None, "Widget be instance of a subclass of BaseWidget or None"
      self.type = self.__class__.__name__
      self.key = key
      self.label = label
      self.widget = widget
      self.description = description
      super().__init__()


  def serialize(self):
      assert self.key is not None, "Please provide at least a key to your Port"
      widgetFragment = {"widget": self.widget.serialize()} if self.widget is not None else {"widget": None}
      return {
        "type": self.type,
        "key": self.key,
        "label" : self.label or self.key.capitalize(),
        "description": self.description,
        **widgetFragment
      }


  def __call__(self, key):
      self.key = key
      return self

  @classmethod
  def fromParameter(cls, param: inspect.Parameter, *args,  label=None, description=None, required=True, **kwargs):
      return cls(
        *args,
        label = label or param.name.capitalize(),
        key = param.name,
        **kwargs
      )


  def __str__(self) -> str:
      return str(self.serialize())