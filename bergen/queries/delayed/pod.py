from bergen.query import DelayedGQL


POD_QUERY = DelayedGQL("""
query Pod($id: ID){
  pod(id: $id){
    id
    status
    name
    unique
    channel
    template {
      id
      provider {
        name
      }
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
}
""")
