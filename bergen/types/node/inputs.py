from bergen.types.node.ports.base import BasePort


class InputsMeta(type):

  def __new__(mcls, name, bases, attrs):
      return super(InputsMeta, mcls).__new__(mcls, name, bases, attrs)


  @property
  def serialized(self):
      return self._serialized

  def __init__(self, name, bases, attrs):
      super(InputsMeta, self).__init__(name, bases, attrs)
      if attrs["__qualname__"] != "Inputs":
          self._serialized = []

          for key, value in attrs.items():
              if isinstance(value, BasePort):
                self._serialized.append(value(key).serialize())
                 




class Inputs(metaclass=InputsMeta):
  pass

class Outputs(metaclass=InputsMeta):
  pass