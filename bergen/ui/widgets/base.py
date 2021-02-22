from bergen.schema import Port

class BaseWidgetMixin:

    def __init__(self, *args, port=None, on_changed, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.port = port
        assert self.port is not None, "Widgets need a keyword argument port to function"
        self.dependencies = self.port.widget.dependencies
        self.on_changed = on_changed
 
    def render(self, keyValuesMap):
        raise NotImplementedError("Please overwrite this in your class")

    @classmethod
    def fromPort(cls, port: Port, **kwargs):
        return cls(port=port, **kwargs)