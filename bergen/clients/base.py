import asyncio
from bergen.hookable.base import Hookable, Hooks
from oauthlib.oauth2.rfc6749.clients.base import Client

from pydantic.main import BaseModel
from bergen.auths.types import User
from typing import Dict
from bergen.wards.graphql.aiohttp import AIOHttpGraphQLWard
from bergen.enums import ClientType, HostProtocol, PostmanProtocol, ProviderProtocol
from bergen.logging import setLogging
from bergen.auths.base import BaseAuthBackend
from bergen.wards.base import BaseWard
from bergen.postmans.base import BasePostman
import logging
from threading import Thread


logger = logging.getLogger(__name__)
import os

def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)


class ArkitektConfig(BaseModel):
    secure: bool
    host: str
    port: int

    def __str__(self) -> str:
        return f"{'Secure' if self.secure else 'Insecure'} Connection to Arkitekt on {self.host}:{self.port}"



class BaseBergen:


    def __init__(self, auth: BaseAuthBackend, config: ArkitektConfig , 
            auto_negotiate=True,
            bind=True,
            log=logging.INFO,
            jupyter=False,
            name=None,
            force_sync = False,
            loop = None,
            client_type: ClientType = ClientType.CLIENT,
            **kwargs) -> None:
        
        if jupyter:
            setLogging(logging.ERROR)
        else:
            print(r"     _               _          _              ____ _ _            _    ")   
            print(r"    / \   _ __ _ __ | |__   ___(_)_ __ ___    / ___| (_) ___ _ __ | |_  ")
            print(r"   / _ \ | '__| '_ \| '_ \ / _ \ | '_ ` _ \  | |   | | |/ _ \ '_ \| __| ")
            print(r"  / ___ \| |  | | | | | | |  __/ | | | | | | | |___| | |  __/ | | | |_  ")
            print(r" /_/   \_\_|  |_| |_|_| |_|\___|_|_| |_| |_|  \____|_|_|\___|_| |_|\__| ")
            print(r"")
            setLogging(log)


        self.running_in_sync = force_sync
        
        self.loop = loop or asyncio.get_event_loop()
        if self.loop.is_running():
            if self.running_in_sync:
                logger.warn("force_insync within event-loop. unexpected errors might be happening")
                import nest_asyncio
                nest_asyncio.apply(self.loop)
            self.loop_is_running = True
        else:
            self.loop_is_running = False

        
        if bind: 
            # We only import this here for typehints
            from bergen.registries.arnheim import set_current_arnheim
            set_current_arnheim(self)

        self.auth = auth
        self.config = config
        self.name = name
        self.client_type = client_type
        self.registered_hooks = Hooks()


        self.token = self.auth.getToken()

        logger.info("We are authorized")
        logger.info(str(config))


        self.host = config.host
        self.port = config.port
        self.protocol = "https" if config.secure else "http"

        self._transcript = None
        self.identifierDataPointMap = {}
        self.identifierWardMap: Dict[str, BaseWard] = {}

        self._provider = None
        self._entertainer = None


        if auto_negotiate == True:
            if self.loop.is_running() and not self.running_in_sync: 
                pass
            else:
               self.negotiate()


        super().__init__() 

    def getLoopAndContext(self):
        return self.loop, self.running_in_sync    


    @property
    def transcript(self):
        assert self._transcript is not None, "We have to negotiate first with our"
        return self._transcript

    def getExtensionSettings(self, extension):
        assert extension in self.transcript.extensions, f"Arnheim seems to have no idea about this Extension {extension}"
        return self.transcript.extensions[extension]

    def getWardForIdentifier(self, identifier):
        if identifier in ["node","template","pod"]:
            return self.main_ward

        if self._transcript is None:
            if self.running_in_sync:
                raise Exception("Not negotiated Error: Please negotiate first or set auto_negotiate=True")
            else:
                raise Exception("You are running in event Loop: Please await self.negotiate_async first or run with 'async with Bergen(....)'")

        if identifier in self.identifierWardMap:
            return self.identifierWardMap[identifier]
        else:
            raise Exception(f"Couldn't find a Ward/Datapoint for Model {identifier}, this mostly results from importing a schema that isn't part of your arkitekts configuration ..Check Documentaiton")


    def getPostmanFromSettings(self, transcript):
        settings = transcript.postman

        if settings.type == PostmanProtocol.RABBITMQ:
            try:
                from bergen.postmans.pika import PikaPostman
                postman = PikaPostman(**settings.kwargs, loop=self.loop, client=self, hooks=self.registered_hooks)
            except ImportError as e:
                logger.error("You cannot use the Pika Postman without installing aio_pika")
                raise e

        elif settings.type == PostmanProtocol.WEBSOCKET:
            try:
                from bergen.postmans.websocket import WebsocketPostman
                postman = WebsocketPostman(**settings.kwargs, loop=self.loop, client=self, hooks=self.registered_hooks)
            except ImportError as e:
                logger.error("You cannot use the Websocket Postman without installing websockets")
                raise e

        else:
            raise Exception(f"Postman couldn't be configured. No Postman for type {settings.type}")

        return postman

    def getProviderFromSettings(self, transcript):
        settings = transcript.provider

        if settings.type == ProviderProtocol.WEBSOCKET:
            try:
                from bergen.provider.websocket import WebsocketProvider
                provider = WebsocketProvider(**settings.kwargs, loop=self.loop, client=self, name=self.name, hooks=self.registered_hooks)
            except ImportError as e:
                logger.error("You cannot use the Websocket Provider without installing websockets")
                raise e

        else:
            raise Exception(f"Provider couldn't be configured. No Provider for type {settings.type}")

        return provider

    def getEntertainerFromSettings(self, transcript):
        settings = transcript.host

        if settings.type == HostProtocol.WEBSOCKET:
            try:
                from bergen.entertainer.websocket import WebsocketHost
                provider = WebsocketHost(**settings.kwargs, loop=self.loop, client=self, hooks=self.registered_hooks)
            except ImportError as e:
                logger.error("You cannot use the Websocket Entertainer without installing websockets")
                raise e

        else:
            raise Exception(f"Entertainer couldn't be configured. No Entertainer for type {settings.type}")

        return provider
    
    async def negotiate_async(self):
        from bergen.constants import NEGOTIATION_GQL
        from bergen.registries.datapoint import get_datapoint_registry

        # Instantiate our Main Ward, this is only for Nodes and Pods
        self.main_ward = AIOHttpGraphQLWard(host=self.host, port=self.port, protocol=self.protocol, token=self.token, loop=self.loop)
        await self.main_ward.configure()

        # We resort escalating to the different client Type protocols
        logger.info(f"Negotiating to be a {self.client_type}")
        self._transcript = await NEGOTIATION_GQL.run_async(ward=self.main_ward, variables={"clientType": self.client_type, "name": self.name})
        

        #Lets create our different Wards 
        
        assert self._transcript.models is not None, "We apparently didnt't get any points"
        
        datapoint_registry = get_datapoint_registry()


        self.identifierDataPointMap = {model.identifier.lower(): model.point for model in self._transcript.models}
        self.identifierWardMap = {model.identifier.lower(): datapoint_registry.createWardForDatapoint(model.point, self) for model in self._transcript.models}

        


        logger.info("Succesfully registered Datapoints") 
        await datapoint_registry.configureWards()
        logger.info("Succesfully connected to Datapoints") 


        self.postman = self.getPostmanFromSettings(self._transcript)
        await self.postman.connect()

        if self.client_type in [ClientType.PROVIDER, ClientType.HOST]:
            logger.warn("We are connected as a Host")
            self._entertainer = self.getEntertainerFromSettings(self._transcript)
            await self._entertainer.connect()

        if self.client_type == ClientType.PROVIDER:
            logger.warn("We are connected as a Provider")
            self._provider = self.getProviderFromSettings(self._transcript)
            await self._provider.connect()



    async def disconnect_async(self, client_type=None):
        await self.main_ward.disconnect()

        if self.postman: await self.postman.disconnect()
        if self._provider: await self._provider.disconnect()
        if self._entertainer: await self._entertainer.disconnect()

        wards = self.identifierWardMap.values()
        for ward in wards:
            await ward.disconnect()


    def negotiate(self, client_type = None):
        self.loop.run_until_complete(self.negotiate_async())


    def getUser(self) -> User:
        return self.auth.getUser()


    def getExtensions(self, service):
        assert service in self._transcript.extensions, "This Service doesnt register Extensions on Negotiate"
        assert self._transcript.extensions[service] is not None, "There are no extensions registered for this Service and this App (see negotiate)"
        return self._transcript.extensions[service]
    
        
    def getWard(self) -> BaseWard:
        return self.main_ward

    def getPostman(self) -> BasePostman:
        return self.postman

    def _repr_html_(self):
        if not self._transcript: return """Unconnected Client"""
        return f"""
            <p> Arnheim Client <p>
            <table>
                <tr>
                    <td> Connected to </td> <td> {self.main_ward.name} </td>
                </tr>
            </table>

        """

    async def __aenter__(self):
        await self.negotiate_async()
        return self


    async def __aexit__(self,*args, **kwargs):
        await self.disconnect_async()

    
    @property
    def provider(self):
        if self._provider:
            return self._provider
        else:
            raise Exception("We are not in Provider mode")

    @property
    def entertainer(self):
        if self._entertainer:
            return self._entertainer
        else:
            raise Exception("We are not in Enterainer mode")

    def hook(self, hook: str, overwrite=False):

        def real_decorator(function):
            self.registered_hooks.addHook(hook, function, overwrite=overwrite)
            return function

        return real_decorator


    def enable(self, *args, **kwargs):
        if self._provider:
            return self.provider.enable(*args, **kwargs)
        else:
            raise Exception("We are not in Provider Mode")

    async def provide_async(self):
        return await self.provider.provide_async()

    def provide(self):
        return self.provider.provide()

