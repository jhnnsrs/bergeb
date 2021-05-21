from abc import abstractmethod
from abc import ABC
import asyncio
from bergen.schema import DataPoint, WardSettings
from bergen.query import  TypedGQL
from typing import TypeVar
from bergen.console import console


T = TypeVar("T")

class WardException(Exception):
    pass

class ConnectionError(Exception):
    pass


class BaseWard(ABC):

    def __init__(self, client, settings: WardSettings, loop=None):
        self.loop = loop or client.loop or asyncio.get_event_loop()

        self.distinct = settings.distinct
        self.needs_negotiation = settings.needsNegotiation
        self.host = settings.host or client.config.host
        self.port = settings.port or client.config.port
        self.protocol = "https" if settings.secure or client.config.secure else "http"

        self.token = client.auth.access_token
        assert self.token is not None, "Cannot create a Ward without acquiring a Token first"


    @abstractmethod
    async def connect(self):
        pass


    async def configure(self):
        try:
            await self.connect()
            if self.needs_negotiation: 
                return await self.negotiate()
            return 
        except:
            console.print_exception()
            raise ConnectionError(f"Ward {self.distinct}: Connection to {self.host}:{self.port} on {self.port} Failed")
        


    def run(self, the_query: TypedGQL, variables: dict = {}, **kwargs):
        return self.loop.run_until_complete(self.run_async(the_query, variables=variables, **kwargs))


    @abstractmethod
    def run_async(self, gql: TypedGQL, variables: dict = {}):
        return gql.cls(**{})


    @abstractmethod
    async def disconnect(self):
        pass


    async def __aenter__(self):
        await self.configure()
        return self


    async def __aexit__(self, *args, **kwargs):
        await self.disconnect()

