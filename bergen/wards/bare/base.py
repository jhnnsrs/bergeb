from abc import ABC
from bergen.query import TypedGQL
import requests
from bergen.schema import WardSettings

from bergen.wards.base import BaseWard, WardException


class BaseGraphQLWard(BaseWard, ABC):
    can_subscribe = False
    

    def __init__(self, client, settings: WardSettings, loop=None) -> None:
        super().__init__(client, settings, loop=loop)
        self._graphql_endpoint = f"{self.protocol}://{self.host}:{self.port}/graphql"
        self._headers = {"Authorization": f"Bearer {self.token}"}

        
    def run(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = the_query.query
        try:
            response = requests.post(self._graphql_endpoint, json={"query": query_node, "variables":variables}, headers=self._headers).json()
            if "errors" in response:
                raise WardException(f"Error: {self._graphql_endpoint} {str(response['errors'])} called with Query {query_node} and variables {variables}")
            return the_query.extract(response["data"])
        except:
            raise




        
