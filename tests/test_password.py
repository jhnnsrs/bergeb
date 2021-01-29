from bergen.enums import GrantType
from bergen.clients.default import Bergen
from bergen.models import Node

client = Bergen(host="p-tnagerl-lab1",
                client_id= "EEjI4z8Gahr6TU6dujnq2Q6pAojcit3iCILF9Ggm",
                client_secret= "Onbmcglhf18rXi0D1pvfeCwnuIGZZV8xpbktzdFXaMs5zpIFG5NJRR2R7pS7RlCgZ6bfiId317XUIrQ1EudJye2WNpZ5jjvbQWul4nyuEECNestHCIUEPCBb3B8DmdwV",
                port=8000,
                name="karl",
                username = "stephane",
                password = "bancelin12345",
                grant_type=GrantType.PASSWORD
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

