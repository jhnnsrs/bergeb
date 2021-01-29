from typing import Generic
from bergen.query import  TypedGQL
from typing import TypeVar


T = TypeVar("T")

class BaseWard(Generic[T]):

    def __init__(self, loop=None):
        self.loop = loop
        self.loop.run_until_complete(self.configure())


    def run(self, gql: TypedGQL, variables: dict = {}):
        return gql.cls(**{})