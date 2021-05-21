
from bergen.queries.delayed.node import DETAIL_NODE_FR
from bergen.schema import Assignation, Node, Peasent, Template, Pod, Provision, Transcript, VartPod, Volunteer
from bergen.query import TypedGQL



 
# Peasent Constants

SERVE_GQL = TypedGQL("""
    mutation Serve($name: String!){
        serve(name: $name){
            id
            name
            
        }
    }
""", Peasent)



OFFER_GQL = TypedGQL("""
    mutation Offer($node: ID!, $params: GenericScalar!, $policy: GenericScalar!){
        offer(node: $node, params: $params, policy: $policy){
            id
            name
            policy 
        }
    }
""", Template)


ACCEPT_GQL = TypedGQL("""
    mutation Accept($template: ID!, $provision: String!){
        accept(template: $template, provision: $provision){
            id
            template {
                node {"""
                + DETAIL_NODE_FR +
                """

                }
            }
        }
    }
""", Pod)


