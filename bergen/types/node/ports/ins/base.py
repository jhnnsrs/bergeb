import inspect
from typing import DefaultDict
from bergen.types.node.widgets.base import BaseWidget


class BaseInPort:

  def __init__(self, type, widget, key=None, label=None, description=None, required=True, primary=False, default=None) -> None:
      print("svesvsev", widget)
      assert isinstance(widget, BaseWidget), "Widget be instance of a subclass of BaseWidget"
      self.type = type
      self.key = key
      self.label = label
      self.widget = widget
      self.description = description
      self.required = required
      self.default = default
      self.primary = primary
      super().__init__()


  def serialize(self):
      assert self.key is not None, "Please provide at least a key to your Port"
      widgetFragment = {"widget": self.widget.serialize()} if self.widget is not None else {}
      return {
        "type": self.type,
        "key": self.key,
        "label" : self.label or self.key.capitalize(),
        "description": self.description,
        "required": self.required,
        "primary": self.primary,
        "default": self.default,
        **widgetFragment
      }


  def __call__(self, key):
      self.key = key
      return self

  @classmethod
  def fromParameter(cls, param: inspect.Parameter, *args,  label=None, description=None, required=True, **kwargs):
      return cls(
        *args,
        default = param.default if not param.default == inspect.Parameter.empty else None,
        label = label or param.name.capitalize(),
        key = param.name,
        required= required,
        **kwargs
      )


  def __str__(self) -> str:
      return str(self.serialize())