from bergen.clients.default import Bergen
from bergen.models import Node, DataPoint

client = Bergen(host="p-tnagerl-lab1",
        port=8000,
        client_id="OyTXRTXNLu6HQpegcch94eQScyrEC85tH0OkstKO", 
        client_secret="nhSPWLVe1Ub2UOEc231KL0KmCQkIpPGubcqJr176wYfSLgLshmJChPmAi7RPs7i1KifjyOmNrPild8VGvkUWfPkvy7dBWfgUPPo6QBTHSTjZluLngrCLg6NiVEF9hbgB",
        name="karl",# if we want to specifically only use pods on this innstance we would use that it in the selector
        )


def test_token():

    assert client.auth.getToken() is not None, "No token provided!"



def test_node_getting():
    nodelist = Node.objects.all()

    assert len(nodelist) > 1, "Your Arnheim Instance seems to have no nodes?"

def test_typed_query():
    from bergen.query import TypedGQL

    nana = TypedGQL('''query Nodes{
        nodes {
            id
        }
    }''', Node).run()

    assert len(nana) > 1, "Your Arnheim instance is not connected?"

