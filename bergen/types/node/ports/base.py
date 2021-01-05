from bergen.types.node.widgets.base import BaseWidget


class BasePort:

  def __init__(self, type, key=None, label=None, widget=None, description=None, required=True, primary=False) -> None:
      self.type = type
      self.key = key
      self.label = label
      self.widget = widget
      assert self.widget is None or isinstance(self.widget, BaseWidget), "Widget must be either none or instance of BaseWidget"
      self.description = description
      self.required = required
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
        **widgetFragment
      }


  def __call__(self, key):
      self.key = key
      return self