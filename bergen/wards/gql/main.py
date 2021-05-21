from abc import abstractmethod
from abc import ABC
import asyncio

from gql.transport.requests import RequestsHTTPTransport
from bergen.console import console
from bergen.wards.base import WardException
from gql.gql import gql

from gql.transport.aiohttp import AIOHTTPTransport
from bergen.schema import DataPoint
from bergen.query import  TypedGQL
from typing import TypeVar

T = TypeVar("T")




class MainWard(ABC):

    def __init__(self, client, loop=None):
        self.loop = loop or client.loop or asyncio.get_event_loop()
        self.host = client.config.host
        self.port = client.config.port
        self.protocol = "https" if client.config.secure else "http"
        self.token = client.auth.access_token

        assert self.token is not None, "Cannot create a Ward without acquiring a Token first"
        self._graphql_endpoint = f"{self.protocol}://{self.host}:{self.port}/graphql"
        self._headers = {"Authorization": f"Bearer {self.token}"}

        self.sync_transport = RequestsHTTPTransport(self._graphql_endpoint, headers=self._headers, verify=True, retries=3)
        self.sync_transport.connect()
        

    def run(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = gql(the_query.query)
        try:
            response = self.sync_transport.execute(query_node, variable_values=variables)
            if response.errors:
                raise WardException(f"Error: {self._graphql_endpoint} {str(response.errors)} called with Query {query_node} and variables {variables}")
            return the_query.extract(response.data)
        except:
            raise

    async def configure(self):
        self.async_transport = AIOHTTPTransport(url=self._graphql_endpoint, headers=self._headers)
        await self.async_transport.connect()


    async def run_async(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = gql(the_query.query)
        try:
            response = await self.async_transport.execute(query_node, variable_values=variables)

            if response.errors:
                raise WardException(f"Ward {self._graphql_endpoint}:" + str(response.errors))
            
            return the_query.extract(response.data)

        except:
            console.print_exception(show_locals=True)
            raise 
            
        
    async def disconnect(self):
        await self.async_transport.close()


    async def __aenter__(self):
        await self.configure()
        return self


    async def __aexit__(self, *args, **kwargs):
        await self.disconnect()

