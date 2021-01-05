from bergen.query import GQL




MARK_GQL = GQL("""
        mutation Mark($message: String!, $assignation: ID!, $level: AssignationStatus) {
            mark(message: $message, assignation: $assignation, level: $level){
                registered
            }
        }
""")


END_GQL = GQL("""
        mutation End($outputs: GenericScalar!, $assignation: ID!) {
            end(outputs: $outputs, assignation: $assignation){
                registered
            }
        }
""")


PROVISION_SUB_GQL = GQL("""
subscription Provide($node: ID!) {
  provide(node: $node, selector: "@kanal/__all__"){
    pod {
      id
    }
    status
  }
}
""")



QUEUE_GQL = GQL("""
    subscription Queue($id: ID!) {
        queue(volunteer: $id){
            id
            status
            volunteer {
                id
                node {
                    id
                    name
                }
                identifier
            }
        }
    }
""")

HOST_GQL = GQL("""
                        subscription Host($pod: ID!) {
                host(pod: $pod){
                    pod {
                        id
                    }
                    id
                    inputs
                }
                }
""")



NODE_QUERY = GQL("""
query Node($id: ID!){
  node(id: $id){
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
""")


