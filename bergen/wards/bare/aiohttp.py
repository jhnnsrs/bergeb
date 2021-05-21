from abc import ABC

import aiohttp
from bergen.wards.bare.base import BaseGraphQLWard
from bergen.wards.base import WardException
from bergen.query import TypedGQL
import logging
from bergen.console import console


class AIOHttpWard(BaseGraphQLWard):
    can_subscribe = False

    async def connect(self):
        self.async_session = aiohttp.ClientSession(headers=self._headers)

    async def negotiate(self):
        if self.needs_negotiation:
            query_node = """
                mutation Negotiate {
                    negotiate
                }
            """
            async with self.async_session.post(self._graphql_endpoint, json={"query": query_node}) as resp:
                result = await resp.json() 
                return result["data"]["negotiate"]
        else:
            return None
    
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