from bergen.clients.default import Bergen
from bergen.models import Node
import pytest
import os

folder_path = os.path.dirname(os.path.abspath(__file__))
print(folder_path)

@pytest.fixture
def backend_client():
    return Bergen(config_path= os.path.join(folder_path, "configs/backend.yaml"), force_new_token=True)

@pytest.fixture
def password_client():
    return Bergen(config_path=os.path.join(folder_path, "configs/password.yaml"),username = "jhnnsrs", password = "gibab42", force_new_token=True)


def test_token_backend(backend_client):
    assert backend_client.auth.getToken() is not None, "No token provided!"


def test_token_password(password_client):

    assert password_client.auth.getToken() is not None, "No token provided!"

def test_node_getting(backend_client):
    nodelist = Node.objects.all(ward=backend_client.main_ward)

    assert len(nodelist) >= 1, "Your Arnheim Instance seems to have no nodes?"

def test_typed_query(password_client):

    from bergen.query import TypedGQL

    nana = TypedGQL('''query Nodes{
        nodes {
            id
        }
    }''', Node).run(ward=password_client.main_ward)

    assert len(nana) >= 1, "Your Arnheim Instance seems to have no nodes?"





