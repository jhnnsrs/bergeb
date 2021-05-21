

from bergen.queries.delayed.node import DETAIL_NODE_FR
from bergen.query import DelayedGQL


TEMPLATE_GET_QUERY = DelayedGQL("""
query Template($id: ID,){
  template(id: $id){
    id
    node {
        """
        + DETAIL_NODE_FR+
        """
    }
  }
}
""")


UPDATE_OR_CREATE_TEMPLATE = DelayedGQL("""
mutation CreateTemplate($node: ID!, $params: GenericScalar){
  createTemplate(node: $node, params: $params){
    id
    node {
        """
        + DETAIL_NODE_FR+
        """
    }
  }
}
""")