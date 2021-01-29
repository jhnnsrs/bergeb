

from bergen.query import DelayedGQL


TEMPLATE_GET_QUERY = DelayedGQL("""
query Template($id: ID,){
  template(id: $id){
    node {
        id
    }
  }
}
""")