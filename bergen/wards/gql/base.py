from abc import ABC
from bergen.schema import DataPoint, WardSettings

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
    

    def __init__(self, client, settings: WardSettings, loop=None) -> None:
        super().__init__(client, settings, loop=loop)
        self._graphql_endpoint = f"{self.protocol}://{self.host}:{self.port}/graphql"
        self._headers = {"Authorization": f"Bearer {self.token}"}

        self.async_transport = None
        self.sync_transport = RequestsHTTPTransport(self._graphql_endpoint, headers=self._headers, verify=True, retries=3)
        self.sync_transport.connect()

    async def negotiate(self):
        assert self.async_transport is not None, "Needs to connect first in order to use async Transport"
        if self.needs_negotiation:
            query_node = gql("""
                mutation Negotiate {
                    negotiate
                }
            """)
            response = await self.async_transport.execute(query_node, variable_values={})
            return response.data["negotiate"]
        else:
            return None
        

    def run(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = gql(the_query.query)
        try:
            response = self.sync_transport.execute(query_node, variable_values=variables)
            if response.errors:
                raise GraphQLException(f"Error: {self._graphql_endpoint} {str(response.errors)} called with Query {query_node} and variables {variables}")
            return the_query.extract(response.data)
        except:
            raise




        
