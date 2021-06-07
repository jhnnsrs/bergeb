from abc import ABC
from bergen.schema import WardSettings

import aiohttp
from bergen.wards.base import GraphQLException, ServiceWard, TokenExpired, WardException
from bergen.query import TypedGQL
import logging
from bergen.console import console

logger = logging.getLogger(__name__)

class AIOHttpWard(ServiceWard):
    can_subscribe = False

    def __init__(self, client, settings: WardSettings, loop=None) -> None:
        super().__init__(client, settings, loop=loop)
        self._graphql_endpoint = f"{self.protocol}://{self.host}:{self.port}/graphql"

    async def connect(self):
        self.async_session = aiohttp.ClientSession(headers=self._headers)

    async def negotiate(self):
        query_node = """
            mutation Negotiate($internal: Boolean) {
                    negotiate(internal: $internal)
            }
        """
        async with self.async_session.post(self._graphql_endpoint, json={"query": query_node, "variables": self.client.config.dict()}) as resp:
            result = await resp.json() 
            return result["data"]["negotiate"]
            
    async def pass_async(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        query_node = the_query.query
        try:
            async with self.async_session.post(self._graphql_endpoint, json={"query": query_node, "variables": variables}) as resp:
                
                if resp.status == 200:
                    result = await resp.json() 
                    logger.debug(f"Received Reply {result}")

                    if "errors" in result:
                        raise GraphQLException(f"Ward {self._graphql_endpoint}:" + str(result["errors"]))

                    return the_query.extract(result["data"])

                if resp.status == 400:
                    raise WardException(await resp.json())


                if resp.status == 403:
                    console.log("Auth token is expired trying to refresh")
                    raise TokenExpired("Token Expired Error")

                raise WardException(f"Unexpected statuscode {resp.status} {resp}")


        except:
            console.print_exception(show_locals=True)
            raise 
            
        
    async def disconnect(self):
        await self.async_session.close()