from abc import abstractmethod
from abc import ABC
import asyncio
import aiohttp
import requests
from bergen.console import console
from bergen.wards.base import WardException
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
        

    def run(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = the_query.query
        try:
            response = requests.post(self._graphql_endpoint, json={"query": query_node, "variables":variables}, headers=self._headers).json()
            if "errors" in response:
                raise WardException(f"Error: {self._graphql_endpoint} {str(response['errors'])} called with Query {query_node} and variables {variables}")
            return the_query.extract(response["data"])
        except:
            raise

    async def configure(self):
        self.async_session = aiohttp.ClientSession(headers=self._headers)


    async def run_async(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = the_query.query
        try:
            async with self.async_session.post(self._graphql_endpoint, json={"query": query_node, "variables": variables}) as resp:
                result = await resp.json() 

                if "errors" in result:
                    raise  WardException(f"Ward {self._graphql_endpoint}:" + str(result["errors"]))

                return the_query.extract(result["data"])

        except:
            console.print_exception(show_locals=True)
            raise 
            
        
    async def disconnect(self):
        await self.async_session.close()


    async def __aenter__(self):
        await self.configure()
        return self


    async def __aexit__(self, *args, **kwargs):
        await self.disconnect()

