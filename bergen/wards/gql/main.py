from abc import abstractmethod
from bergen.console import console
from bergen.wards.base import MainWard, GraphQLException, TokenExpired
from gql.gql import gql

from gql.transport.aiohttp import AIOHTTPTransport
from bergen.schema import DataPoint
from bergen.query import  TypedGQL
from typing import TypeVar

T = TypeVar("T")


class GQLMainWard(MainWard):

    def __init__(self, client, loop=None):
        super().__init__(client, loop=loop)
        self._graphql_endpoint = f"{self.protocol}://{self.host}:{self.port}/graphql"
        
    async def connect(self):
        self.async_transport = AIOHTTPTransport(url=self._graphql_endpoint, headers=self._headers)
        await self.async_transport.connect()


    async def pass_async(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = gql(the_query.query)
        try:
            try:
                response = await self.async_transport.execute(query_node, variable_values=variables)
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


