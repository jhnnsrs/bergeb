from abc import ABC

from gql.gql import gql
from gql.transport.requests import RequestsHTTPTransport
from bergen.wards.base import BaseWard, WardException
from bergen.query import GQL, TypedGQL
from gql.transport.aiohttp import AIOHTTPTransport
import logging
from gql.transport.aiohttp import log as aiohttp_logger
from gql.transport.requests import log as requests_logger
aiohttp_logger.setLevel(logging.WARNING)
requests_logger.setLevel(logging.WARNING)
import asyncio
from gql import Client, gql


class GraphQLException(WardException):
    pass


class BaseGraphQLWard(BaseWard, ABC):
    can_subscribe = False
    

    def __init__(self, port=8000, host="localhost", protocol="http", token=None, loop = None) -> None:
        self._graphql_endpoint = f"{protocol}://{host}:{port}/graphql"
        self._token = token
        self._headers = {"Authorization": f"Bearer {self._token}"}
        
        self.sync_transport = RequestsHTTPTransport(self._graphql_endpoint, headers=self._headers, verify=True, retries=3)
        self.sync_transport.connect()
        
        super().__init__(loop=loop)

    
    def run(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        if self.loop.is_running():
            # We are alredy doing some weird shit
            query_node = gql(the_query.query)
            response = self.sync_transport.execute(query_node, variable_values=variables)
            if response.errors:
                raise GraphQLException(f"Error: {self._graphql_endpoint} {str(response.errors)}")
            return the_query.extract(response.data)

        else:
            return self.loop.run_until_complete(self.run_async(the_query, variables=variables, **kwargs))



        
