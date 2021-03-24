from bergen.queries.delayed.node import DETAIL_NODE_FR
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
      node {"""

+ DETAIL_NODE_FR + 

"""
      }
    }
  }
}
""")
