from bergen.query import DelayedGQL


NODE_QUERY = DelayedGQL("""
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


NODE_FILTER_QUERY = DelayedGQL("""
query NodeFilter($name: String){
  nodes(name: $name){
    id
    name
    repository {
      name
    }
    description
  }
}
""")


CREATE_NODE_MUTATION = DelayedGQL("""
  mutation CreateNodeMutation($description: String!, $inputs: [PortInputType]!, $outputs: [PortInputType]!, $package: String!, $interface: String!, $name: String!){
  createNode(description: $description, inputs: $inputs, outputs: $outputs, package:$package, interface: $interface, name: $name){
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