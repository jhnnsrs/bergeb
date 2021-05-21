import logging
from abc import ABC

from bergen.console import console
from bergen.query import GQL, TypedGQL
from bergen.wards.base import BaseWard
from bergen.wards.gql.base import BaseGraphQLWard, GraphQLException
from gql.gql import gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.aiohttp import log as aiohttp_logger
from gql.transport.requests import RequestsHTTPTransport

aiohttp_logger.setLevel(logging.WARNING)


class AIOHttpGraphQLWard(BaseGraphQLWard):
    can_subscribe = False

    async def connect(self):
        self.async_transport = AIOHTTPTransport(url=self._graphql_endpoint, headers=self._headers)
        await self.async_transport.connect()

    async def negotiate(self):
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
    

    async def run_async(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = gql(the_query.query)
        try:
            response = await self.async_transport.execute(query_node, variable_values=variables)

            if response.errors:
                raise GraphQLException(f"Ward {self._graphql_endpoint}:" + str(response.errors))
            
            return the_query.extract(response.data)

        except:
            console.print_exception(show_locals=True)
            raise 
            
        
    async def disconnect(self):
        await self.async_transport.close()
