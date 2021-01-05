
class BaseWidget:

  def __init__(self, type) -> None:
      assert type is not None, "Please provide a Valid Type for the Widget"
      self.type = type
      super().__init__()


  def serialize(self):
      return {
          "type": type

      }


  def deserialize(self, registry):
      raise NotImplementedError("Please specifiy this")
