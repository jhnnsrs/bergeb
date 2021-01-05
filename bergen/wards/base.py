from typing import Generic
from bergen.query import  TypedGQL
from typing import TypeVar


T = TypeVar("T")

class BaseWard(Generic[T]):

    def __init__(self, port=8000, host="localhost", protocol="http", token=None) -> None:
        self.port = port
        self.host = host
        self.protocol = protocol
        self.token = token
        super().__init__()


    def run(self, gql: TypedGQL, variables: dict = {}):
        return gql.cls(**{})