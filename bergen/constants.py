
from bergen.schema import Assignation, Node, Peasent, PeasentTemplate, Pod, Provision, Transcript, VartPod, Volunteer
from bergen.query import TypedGQL


NEGOTIATION_GQL = TypedGQL("""

  mutation Negotiate($clientType: ClientType!, $local: Boolean!) {
  negotiate(clientType: $clientType) {
    array {
      path
      params
    }
    timestamp
    user {
        username
    }
    extensions
    models {
        identifier
        point {
            name
            host (local: $local)
            port
            type
        }
    }
    postman {
        type
        kwargs
    }
    points {
      host
      name
      models {
        identifier
        extenders
      }
    }
    
  }
  }
""", Transcript)

 
# Peasent Constants

SERVE_GQL = TypedGQL("""
    mutation Serve($name: String!){
        serve(name:$name){
            id
            name
            
        }
    }
""", Peasent)




OFFER_GQL = TypedGQL("""
    mutation Offer($node: ID!, $params: GenericScalar!, $peasent: ID!){
        offer(node: $node, params: $params, peasent: $peasent ){
            id
            name 
        }
    }
""", PeasentTemplate)


ACCEPT_GQL = TypedGQL("""
    mutation AcceptMutation($peasent: ID!, $template: ID!){
        accept(peasent: $peasent, template: $template){
            id
        }
        }
""", Pod)











VOLUNTEER_GQL = TypedGQL("""
        mutation Volunteer($nodeid: ID!, $name: String!, $version: String!){
            volunteer(node: $nodeid, name: $name, version: $version){
                node {
                    id
                    name
                    package
                }
                identifier
                id
            }
        }
    """, Volunteer)



MARK_GQL = TypedGQL("""
        mutation Mark($message: String!, $assignation: ID!, $level: AssignationStatus) {
            mark(message: $message, assignation: $assignation, level: $level){
                registered
            }
        }
""", dict)


END_GQL = TypedGQL("""
        mutation End($outputs: GenericScalar!, $assignation: ID!) {
            end(outputs: $outputs, assignation: $assignation){
                registered
            }
        }
""", dict)

YIELD_GQL = TypedGQL("""
        mutation Yield($outputs: GenericScalar!, $assignation: ID!) {
            yield(outputs: $outputs, assignation: $assignation){
                registered
            }
        }
""", dict)


QUEUE_GQL = TypedGQL("""
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
""", VartPod)


HOST_GQL = TypedGQL("""
                        subscription Host($pod: ID!) {
                host(pod: $pod){
                    pod {
                        id
                    }
                    id
                    inputs
                }
                }
""", Assignation)


PROVIDE_GQL = TypedGQL("""
        subscription Provide($reference: String!, $node: ID!, $selector: SelectorInput!){
            provide(node: $node , selector: $selector, reference: $reference){
                pod {
                    id
                    status
                }
                node {
                    name
                }
                reference
                status
                statusmessage

            }
        }      
    """, Provision)



ASSIGN_GQL = TypedGQL("""
        subscription Assignation($inputs: GenericScalar!, $pod: ID!, $reference: String!) {
            assign(inputs: $inputs, pod: $pod, reference: $reference){
                inputs
                outputs
                status
                statusmessage
            }
        }     
""", Assignation)