from bergen.schema import DataModel
from bergen.query import TypedGQL


HOST_GQL = TypedGQL("""
    mutation Host($identifier: String!, $extenders: [String]){
        host(identifier: $identifier, extenders: $extenders){
            id
            identifier
            extenders
            point {
                inward
            }
        }
    }
""", DataModel)