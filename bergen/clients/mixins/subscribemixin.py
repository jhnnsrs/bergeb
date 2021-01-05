from typing import TypeVar
from bergen.wards.base import BaseWard
from bergen.query import TypedGQL

T = TypeVar("T")

class SubscribeMixIn:


    def subscribe(self, gql: TypedGQL[T], variables: dict= {}, force_endpoint=None) -> T:
        assert gql.type == "subscription", "This is not a mutation!"
        identifier = force_endpoint or gql.cls.Meta.identifier
        ward: BaseWard = self.getClientForIdentifier(identifier)
        return ward.subscribe(gql, variables=variables)