from flow.diagram import Diagram
from flow.graphql.queries.graph import GET_GRAPH
from typing import Optional
from bergen.types.model import ArnheimModel


class Graph(ArnheimModel):
    id: Optional[int]
    diagram: Optional[Diagram]

    class Meta:
        identifier = "graph"
        get = GET_GRAPH
