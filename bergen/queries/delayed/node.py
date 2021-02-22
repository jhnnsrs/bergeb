from bergen.query import DelayedGQL


INPUTS_FR = """
  inputs {
    __typename
      key
      required
      description
      widget {
        __typename
        dependencies
        ... on QueryWidgetType {
          query  
        }
      }
      label
      ... on ModelPortType {
        identifier
      }
      ... on IntPortType {
        default
      }
  }
"""


OUTPUTS_FR = """
  outputs {
    __typename
      key
      required
      description
      ... on ModelPortType {
        identifier
      }
  }
"""


NODE_QUERY = DelayedGQL("""
query Node($id: ID, $package: String, $interface: String){
  node(id: $id, package: $package, interface: $interface){
    id
    name
    image
""" + INPUTS_FR + """
""" + OUTPUTS_FR + """
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
  mutation CreateNodeMutation($description: String!, $inputs: [InPortInputType]!, $outputs: [OutPortInputType]!, $package: String!, $interface: String!, $name: String!){
  createNode(description: $description, inputs: $inputs, outputs: $outputs, package:$package, interface: $interface, name: $name){
    id
    name
    image
""" + INPUTS_FR + """
""" + OUTPUTS_FR + """
  }
}
""")


UPDATE_OR_CREATE_NODE = DelayedGQL("""
  mutation UpdateOrCreateNode($description: String!, $inputs: [InPortInputType]!, $outputs: [OutPortInputType]!, $package: String!, $interface: String!, $name: String!){
  updateOrCreateNode(description: $description, inputs: $inputs, outputs: $outputs, package:$package, interface: $interface, name: $name){
     id
    name
    image
""" + INPUTS_FR + """
""" + OUTPUTS_FR + """
  }
}
""")