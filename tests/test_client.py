from bergen.clients.default import Bergen
from bergen.schema import Node, DataPoint

client = Bergen(host="p-tnagerl-lab1",
        port=8000,
        client_id="y1W8JK5OgpAexf68eqbHIx60228rTBc4moNlaKYN", 
        client_secret="ovChuVgIFFQcNT3buPbm5AVjGCJGHBQZOQTqhvzwP02IllfJRVj17efit6aGqPcd01AJPY1SCc8kTBM22pistp8A1BRQRmtgX9Nycd2LcN1YEduhjpSY9mq5Pm2nV0xi",
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

