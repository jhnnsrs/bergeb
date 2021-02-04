

from bergen.query import DelayedGQL


TEMPLATE_GET_QUERY = DelayedGQL("""
query Template($id: ID,){
  template(id: $id){
    id
    node {
        id
        name
        image
        inputs {
          __typename
          key
          required
          ... on ModelPortType {
            identifier
          }
        }
        outputs {
          __typename
          key
          required
          ... on ModelPortType {
            identifier
          }
        }
    }
  }
}
""")