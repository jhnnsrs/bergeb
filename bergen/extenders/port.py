from typing import Any, Callable, Mapping
import logging

logger = logging.getLogger(__name__)

class ArgPortExtender:

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._widget = None

    def buildWidget(self, **kwargs):
        try:
            from bergen.ui.widgets import QueryWidget, SliderWidget, IntWidget, VoidWidget, BaseWidgetMixin

            typeWidgetMap: Mapping[str, Callable[[Any], BaseWidgetMixin]] = {
                "QueryWidgetType": lambda port: QueryWidget.fromPort(port, **kwargs),
                "SliderWidgetType": lambda port: SliderWidget.fromPort(port, **kwargs),
                "IntWidgetType": lambda port: IntWidget.fromPort(port, **kwargs),
            }

            widgetBuilder = typeWidgetMap.get(self.widget.TYPENAME, lambda port: VoidWidget.fromPort(port, **kwargs))
            self._widget = widgetBuilder(self)
            return self._widget

        except ImportError as e:
            logger.error("Please install PyQt5 in Order to use widgets")
            raise e
    
    def __call__(inputs: dict, provider="vard"):
        logger.info("Called with inputs")

        logger.info("Serializing Inputs")


    def _repr_html_(self):
        string = f"{self.TYPENAME} with {self.key}"

        return string


class KwargPortExtender:

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._widget = None

    def buildWidget(self, **kwargs):
        try:
            from bergen.ui.widgets import QueryWidget, SliderWidget, IntWidget, VoidWidget, BaseWidgetMixin

            typeWidgetMap: Mapping[str, Callable[[Any], BaseWidgetMixin]] = {
                "QueryWidgetType": lambda port: QueryWidget.fromPort(port, **kwargs),
                "SliderWidgetType": lambda port: SliderWidget.fromPort(port, **kwargs),
                "IntWidgetType": lambda port: IntWidget.fromPort(port, **kwargs),
            }

            widgetBuilder = typeWidgetMap.get(self.widget.TYPENAME, lambda port: VoidWidget.fromPort(port, **kwargs))
            self._widget = widgetBuilder(self)
            return self._widget

        except ImportError as e:
            logger.error("Please install PyQt5 in Order to use widgets")
            raise e
    
    def __call__(inputs: dict, provider="vard"):
        logger.info("Called with inputs")

        logger.info("Serializing Inputs")


    def _repr_html_(self):
        string = f"{self.TYPENAME} with {self.key}"

        return string


class ReturnPortExtender:

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


    def _repr_html_(self):
        string = f"{self.TYPENAME} with {self.key}"

        return string