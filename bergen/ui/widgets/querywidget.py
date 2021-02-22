from bergen.query import ListQuery, QueryList, TypedGQL
from typing import Any, Optional
from bergen.types.object import ArnheimObject
from bergen.schema import Port
from bergen.ui.widgets.base import BaseWidgetMixin
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QWidget
from bergen.registries.arnheim import get_current_arnheim

class SelectorItem(ArnheimObject):
    value: Optional[Any]
    label: Optional[str]




class QueryWidget(BaseWidgetMixin, QWidget):
    query = None


    def __init__(self, *args, query=None, identifier=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.query = self.query or query
        assert self.query is not None

        self.ward = get_current_arnheim().getWardForIdentifier(identifier)
        self.model_selector = QComboBox()
        self.model_selector.currentIndexChanged.connect(self.indexChanged)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.model_selector)
        self.current_value = None
        self.setLayout(self.layout)


    def indexChanged(self, index):
        value = self.items[index].value
        if value == self.current_value:
            return

        self.current_value = value
        print(self.current_value)
        if self.on_changed: self.on_changed(value)


    def render(self, keyValueMap):
        self.model_selector.clear()
        self.items = QueryList(self.query, SelectorItem).run(ward=self.ward, variables=keyValueMap)
        for item in self.items:
            self.model_selector.addItem(item.label)
        
            
    @classmethod
    def fromPort(cls, port: Port, **kwargs):
        assert port.widget.query is not None, "Please request query on QueryWidgetType to build a QueryWidget"
        return cls(port=port, query=port.widget.query, identifier = port.identifier, **kwargs)


