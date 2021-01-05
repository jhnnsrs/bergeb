
from typing import TypeVar
from bergen.query import TypedGQL
from bergen.wards.base import BaseWard


T = TypeVar("T")



class QueryMixIn:


    def query(self, gql: TypedGQL[T], variables: dict= {}, force_endpoint=None) -> T:
        assert gql.type == "query", "This is not a query!"
        identifier = force_endpoint or gql.cls.Meta.identifier
        ward: BaseWard = self.getClientForIdentifier(identifier)
        return gql.run(gql, variables=variables, ward=ward)


    def mutate(self, gql: TypedGQL[T], variables: dict= {}, force_endpoint=None) -> T:
        assert gql.type == "mutation", "This is not a mutation!"
        identifier = force_endpoint or gql.cls.Meta.identifier  
        ward: BaseWard = self.getClientForIdentifier(identifier)
        return gql.run(gql, variables=variables, ward=ward)
