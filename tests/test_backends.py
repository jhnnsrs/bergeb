from bergen.enums import GrantType
from bergen.clients.default import Bergen
from bergen.models import Node, DataPoint
import pytest


@pytest.fixture
def backend_client():
    return Bergen(host="p-tnagerl-lab1",
        port=8000,
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        name="karl",# if we want to specifically only use pods on this innstance we would use that it in the selector
        )

@pytest.fixture
def password_client():
    return Bergen(host="p-tnagerl-lab1",
                    client_id= "EEjI4z8Gahr6TU6dujnq2Q6pAojcit3iCILF9Ggm",
                    client_secret= "Onbmcglhf18rXi0D1pvfeCwnuIGZZV8xpbktzdFXaMs5zpIFG5NJRR2R7pS7RlCgZ6bfiId317XUIrQ1EudJye2WNpZ5jjvbQWul4nyuEECNestHCIUEPCBb3B8DmdwV",
                    port=8000,
                    name="karl",
                    username = "stephane",
                    password = "bancelin12345",
                    grant_type=GrantType.PASSWORD
    )


def test_token_backend(backend_client):
    assert backend_client.auth.getToken() is not None, "No token provided!"


def test_token_password(password_client):

    assert password_client.auth.getToken() is not None, "No token provided!"

def test_node_getting(backend_client):
    nodelist = Node.objects.all(ward=backend_client.main_ward)

    assert len(nodelist) > 1, "Your Arnheim Instance seems to have no nodes?"

def test_typed_query(password_client):

    from bergen.query import TypedGQL

    nana = TypedGQL('''query Nodes{
        nodes {
            id
        }
    }''', Node).run(ward=password_client.main_ward)

    assert len(nana) > 1, "Your Arnheim instance is not connected?"





