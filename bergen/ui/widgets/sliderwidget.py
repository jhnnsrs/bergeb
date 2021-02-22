from PyQt5.QtCore import Qt
from bergen.query import ListQuery, QueryList, TypedGQL
from typing import Any, Optional
from bergen.types.object import ArnheimObject
from bergen.schema import Port
from bergen.ui.widgets.base import BaseWidgetMixin
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSlider, QWidget
from bergen.registries.arnheim import get_current_arnheim

class SelectorItem(ArnheimObject):
    value: Optional[Any]
    label: Optional[str]




class SliderWidget(BaseWidgetMixin, QWidget):
    query = None


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.sld = QSlider(Qt.Horizontal, self)
        self.label = QLabel(str(self.port.default))
        self.sld.setRange(0, 100)
        self.sld.setFocusPolicy(Qt.NoFocus)
        self.sld.setPageStep(5)
        self.sld.setValue(self.port.default)
        self.sld.valueChanged.connect(self.valueChanged)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.sld)
        self.layout.addWidget(self.label)
        self.current_value = None
        self.setLayout(self.layout)


    def valueChanged(self, value):
        if value == self.current_value:
            return

        self.current_value = value
        self.label.setText(str(self.current_value))
        if self.on_changed: self.on_changed(value)


    def render(self, keyValueMap):
        pass
        
     
    @classmethod
    def fromPort(cls, port: Port, **kwargs):
        return cls(port=port, **kwargs)


