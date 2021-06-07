from abc import abstractmethod
from abc import ABC
import asyncio
from bergen.auths.base import BaseAuthBackend
from bergen.schema import DataPoint, WardSettings
from bergen.query import  TypedGQL
from typing import TypeVar
from bergen.console import console


T = TypeVar("T")

class WardException(Exception):
    pass

class GraphQLException(WardException):
    pass

class ConnectionError(Exception):
    pass

class TokenExpired(ConnectionError):
    pass


class BaseWard(ABC):

    def __init__(self, client, loop=None):
        self.loop = loop or client.loop or asyncio.get_event_loop()
        self.client = client
        self.auth: BaseAuthBackend = client.auth
        assert self.auth.access_token is not None, "Cannot create a Ward without acquiring a Token first"
        self._headers = {"Authorization": f"Bearer {self.auth.access_token}"}

    @abstractmethod
    async def connect(self):
        """Everytime we need to reastablish a connection because of a Token Refersh"""
        pass

    @abstractmethod
    async def configure(self):
        """The initial connection attempt (also negotiation can happen here)"""
        pass


    @abstractmethod
    async def disconnect(self):
        """CleanUp"""
        pass


    async def run(self, gql: TypedGQL, variables: dict = {}):
        try:
            return await self.pass_async(gql, variables=variables)

        except TokenExpired:
            console.print_exception()

            self.auth.refetch()
            self._headers = {"Authorization": f"Bearer {self.auth.access_token}"}

            await self.disconnect()
            await self.connect()

            return await self.pass_async(gql, variables=variables)

        except:
            console.print_exception(show_locals=True)
            raise



    @abstractmethod
    def pass_async(self, gql: TypedGQL, variables: dict = {}):
        return gql.cls(**{})




class ServiceWard(BaseWard):

    def __init__(self, client, settings: WardSettings, loop=None):
        self.distinct = settings.distinct
        self.needs_negotiation = settings.needsNegotiation
        self.host = settings.host or client.config.host
        self.port = settings.port or client.config.port
        self.protocol = "https" if settings.secure or client.config.secure else "http"
        super().__init__(client, loop=loop)

    async def configure(self):
        try:
            await self.connect()
            if self.needs_negotiation: 
                return await self.negotiate()
            return 
        except:
            console.print_exception()
            raise ConnectionError(f"Ward {self.distinct}: Connection to {self.host}:{self.port} on {self.port} Failed")



class MainWard(BaseWard):

    def __init__(self, client, loop=None):
        self.host = client.config.host
        self.port = client.config.port
        self.protocol = "https" if client.config.secure else "http"
        super().__init__(client, loop=loop)

    async def configure(self):
        try:
            await self.connect()
        except:
            console.print_exception()
            raise ConnectionError(f"BaseWard: Connection to {self.host}:{self.port} on {self.port} Failed")
