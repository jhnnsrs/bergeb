from bergen.wards.base import ServiceWard, TokenExpired, GraphQLException
from bergen.schema import WardSettings
import logging
from abc import ABC

from bergen.console import console
from bergen.query import GQL, TypedGQL
from gql.gql import gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.aiohttp import log as aiohttp_logger
from gql.transport.requests import RequestsHTTPTransport

aiohttp_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class AIOHttpGraphQLWard(ServiceWard):
    can_subscribe = False

    def __init__(self, client, settings: WardSettings, loop=None) -> None:
        super().__init__(client, settings, loop=loop)
        self._graphql_endpoint = f"{self.protocol}://{self.host}:{self.port}/graphql"

    async def connect(self):
        self.async_transport = AIOHTTPTransport(url=self._graphql_endpoint, headers=self._headers)
        await self.async_transport.connect()

    async def negotiate(self):
        query_node = gql("""
                mutation Negotiate($internal: Boolean) {
                    negotiate(internal: $internal)
                }
            """)
        response = await self.async_transport.execute(query_node, variable_values=self.client.config.dict())
        return response.data["negotiate"]
    
    async def pass_async(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = gql(the_query.query)
        try:
            try:
                response = await self.async_transport.execute(query_node, variable_values=variables)#
                logger.debug(f"Received Reply {response}")
            except Exception as e:
                console.print_exception(show_locals=True)
                raise TokenExpired(f"Token Expired {e}")
                
            if response.errors:
                raise GraphQLException(f"Ward {self._graphql_endpoint}:" + str(response.errors))
            
            return the_query.extract(response.data)

        except:
            console.print_exception(show_locals=True)
            raise 
            
        
    async def disconnect(self):
        await self.async_transport.close()
