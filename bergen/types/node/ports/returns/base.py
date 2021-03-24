import inspect
from typing import DefaultDict
from bergen.types.node.widgets.base import BaseWidget


class BaseReturnPort:

  def __init__(self, type, key=None, label=None, description=None) -> None:
      self.type = type
      self.key = key
      self.label = label
      self.description = description
      super().__init__()


  def serialize(self):
      assert self.key is not None, "Please provide at least a key to your Port"
      return {
        "type": self.type,
        "key": self.key,
        "label" : self.label or self.key.capitalize(),
        "description": self.description,
      }


  def __call__(self, key):
      self.key = key
      return self


  def __str__(self) -> str:
      return str(self.serialize())