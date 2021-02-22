
class BaseWidget:

  def __init__(self, type, dependencies=None) -> None:
      self.type = type
      self.dependencies = dependencies or []
      assert isinstance(self.dependencies, list), "Depencies must be a list of strings"

      super().__init__()


  def serialize(self):

      return {
          "type": self.type,
          "dependencies": self.dependencies,
          **self.params()

      }

  def params(self, port):
      return {}

