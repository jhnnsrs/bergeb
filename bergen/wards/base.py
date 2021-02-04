from abc import abstractmethod
from abc import ABC
from bergen.query import  TypedGQL
from typing import TypeVar
import namegenerator

T = TypeVar("T")

class WardException(Exception):
    pass




class BaseWard(ABC):

    def __init__(self, loop=None, name = None):
        self.loop = loop
        self.name = name or namegenerator.gen()

    @abstractmethod
    async def configure(self):
        pass

    def run(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        return self.loop.run_until_complete(self.run_async(the_query, variables=variables, **kwargs))

    @abstractmethod
    def run_async(self, gql: TypedGQL, variables: dict = {}):
        return gql.cls(**{})