
class BaseWidget:

  def __init__(self, dependencies=None) -> None:
      self.type = self.__class__.__name__
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

