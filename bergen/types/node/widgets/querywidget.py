


from bergen.types.node.widgets.base import BaseWidget


class QueryWidget(BaseWidget):

    def __init__(self, query: str, **kwargs) -> None:
        super().__init__("query", **kwargs)
        self.query = query
        #TODO: Inspect if widgets dependencies are okay for that query

    def params(self):
        return { "query": self.query}