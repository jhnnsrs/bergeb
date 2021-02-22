from PyQt5.QtCore import Qt
from bergen.query import ListQuery, QueryList, TypedGQL
from typing import Any, Optional, Text
from bergen.types.object import ArnheimObject
from bergen.schema import Port
from bergen.ui.widgets.base import BaseWidgetMixin
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QSlider, QTextEdit, QWidget
from bergen.registries.arnheim import get_current_arnheim


class VoidWidget(BaseWidgetMixin, QWidget):
    query = None


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.text = QLineEdit("Void widget")
        self.text.textChanged.connect(self.valueChanged)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.text)
        self.current_value = None
        self.setLayout(self.layout)


    def valueChanged(self):
        value = self.text.text()
        if value == self.current_value:
            return

        self.current_value = value
        if self.on_changed: self.on_changed(value)


    def render(self, keyValueMap):
        pass
        
     
    @classmethod
    def fromPort(cls, port: Port, **kwargs):
        return cls(port=port, **kwargs)


