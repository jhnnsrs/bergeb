from abc import ABC
import re
from bergen.wards.base import BaseWard
from bergen.query import GQL, TypedGQL
import requests
from gql.transport.aiohttp import AIOHTTPTransport
import logging
from gql.transport.aiohttp import log as aio_logger
aio_logger.setLevel(logging.WARNING)
from gql import gql, Client

class GraphQlException(Exception):
    pass

class ProtocolException(GraphQlException):
    pass

class SyntaxException(GraphQlException):
    pass

class QueryException(GraphQlException):
    pass


class BaseGraphQLWard(BaseWard, ABC):
    can_subscribe = False
    

    def __init__(self, port=8000, host="localhost", protocol="ws", token=None, loop = None) -> None:
        self._graphql_endpoint = f"{protocol}://{host}:{port}/graphql"
        self._token = token
        self._headers = {"Authorization": f"Bearer: {self._token}"}
        
        self.transport =  AIOHTTPTransport(url=self._graphql_endpoint, headers=self._headers)
        self.client = Client(
        transport=self.transport, fetch_schema_from_transport=True,
        )
        
        super().__init__(loop=loop)


    async def configure(self):
        pass



    def run(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        gql_query = gql(the_query.query)
        if self.loop.is_running():
            result = self.loop.run_until_complete(self.client.execute_async(gql_query, variable_values = variables))
        else:
            result = self.client.execute(gql_query, variable_values = variables)
        return the_query.extract(result)

    async def run_async(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        
        transport =  AIOHTTPTransport(url=self._graphql_endpoint, headers=self._headers)
        client = Client(
        transport=transport, fetch_schema_from_transport=True,
        )

        gql_query = gql(the_query.query)
        result = await client.execute_async(gql_query, variable_values = variables)
        return the_query.extract(result)