from bergen.query import DelayedGQL


INPUTS_FR = """
  args {
    __typename
      key
      required
      description
      widget {
        __typename
        dependencies
        ... on QueryWidget {
          query  
        }
      }
      label
      ... on ModelArgPort {
        identifier
      }
      ... on IntArgPort {
        default
      }
  }
  kwargs {
    __typename
      key
      required
      description
      widget {
        __typename
        dependencies
        ... on QueryWidget {
          query  
        }
      }
      label
      ... on ModelKwargPort {
        identifier
      }
      ... on IntKwargPort {
        default
      }
  }
"""


OUTPUTS_FR = """
  returns {
    __typename
      key
      description
      ... on ModelReturnPort {
        identifier
      }
  }
"""



DETAIL_NODE_FR = """
  name
  package
  interface
  id
  type
""" + INPUTS_FR + OUTPUTS_FR 


NODE_QUERY = DelayedGQL("""
query Node($id: ID, $package: String, $interface: String){
  node(id: $id, package: $package, interface: $interface){
    """+ DETAIL_NODE_FR +"""
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
  mutation CreateNodeMutation(
    $description: String!,
    $args: [ArgPortInput]!,
    $kwargs: [KwargPortInput]!,
    $returns: [ReturnPortInput]!,
    $package: String!, $interface: String!,
    $name: String!
    $type: NodeTypeInput){
  createNode(description: $description, args: $args, kwargs: $kwargs, returns: $returns, package:$package, interface: $interface, name: $name, type: $type){
    """+ DETAIL_NODE_FR +"""
  }
}
""")


UPDATE_OR_CREATE_NODE = DelayedGQL("""
  mutation CreateNodeMutation($description: String!, $args: [ArgPortInput]!, $kwargs: [KwargPortInput]!, $returns: [ReturnPortInput]!, $interface: String!, $name: String!, $type: NodeTypeInput){
  createNode(description: $description, args: $args, kwargs: $kwargs, returns: $returns, interface: $interface, name: $name, type: $type){
    """+ DETAIL_NODE_FR +"""
  }
}
""")