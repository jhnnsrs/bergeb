import asyncio
from bergen.registries.ward import get_ward_registry
from bergen.wards.default import MainWard
from bergen.config.types import ArkitektConfig, HerreConfig
from bergen.schemas.herre.types import User
from bergen.schema import Transcript
from bergen.hookable.base import Hooks
from pydantic.main import BaseModel
from typing import Dict
from bergen.enums import ClientType, HostProtocol, PostmanProtocol, ProviderProtocol
from bergen.logging import setLogging
from bergen.auths.base import BaseAuthBackend
from bergen.wards.base import BaseWard
from bergen.postmans.base import BasePostman
import logging

from bergen.console import console
from rich.panel import Panel
from rich.table import Table

from rich import pretty
pretty.install()
from rich.traceback import install
install()

logger = logging.getLogger(__name__)
import os


class SafetyError(Exception):
    pass


class BaseBergen:


    def __init__(self, auth: BaseAuthBackend, config: ArkitektConfig , 
            bind=True,
            log=logging.INFO,
            client_type: ClientType = ClientType.CLIENT,
            log_stream=False,
            auto_connect=False,
            capture_exceptions=False,
            **kwargs) -> None:
        
        
        setLogging(log, log_stream=log_stream)

       
        if bind: 
            # We only import this here for typehints
            from bergen.registries.client import set_current_client
            set_current_client(self)


        self.auth = auth
        self.auth.login()

        self.config = config
        self.client_type = client_type
        self.capture_exceptions=False

        self.registered_hooks = Hooks()

        self.host = config.host
        self.port = config.port
        self.is_iternal = config.internal
        self.protocol = "https" if config.secure else "http"

        self._transcript = None
        self.identifierDataPointMap = {}
        self.identifierWardMap: Dict[str, BaseWard] = {}

        self._provider = None
        self._entertainer = None
        self.negotiate_additionals = {}

        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            console.log("[yellow] Creating New EventLoop in This Thread")
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        if auto_connect:
            self.negotiate()


    @property
    def transcript(self):
        assert self._transcript is not None, "We have to negotiate first with our"
        return self._transcript

    def getWardForIdentifier(self, identifier):
        if identifier in ["node","template","pod"]:
            return self.main_ward

        if self._transcript is None:
            raise Exception("Not Negotiated yet!")

        if identifier in self.identifierWardMap:
            return self.identifierWardMap[identifier]
        else:
            raise Exception(f"Couldn't find a Ward/Datapoint for Model {identifier}, this mostly results from importing a schema that isn't part of your arkitekts configuration ..Check Documentaiton")


    def getPostmanFromSettings(self, transcript: Transcript):
        settings = transcript.postman

        if settings.type == PostmanProtocol.RABBITMQ:
            try:
                from bergen.postmans.pika import PikaPostman
                postman = PikaPostman(self, **settings.kwargs, hooks=self.registered_hooks)
            except ImportError as e:
                logger.error("You cannot use the Pika Postman without installing aio_pika")
                raise e

        elif settings.type == PostmanProtocol.WEBSOCKET:
            try:
                from bergen.postmans.websocket import WebsocketPostman
                postman = WebsocketPostman(self, **settings.kwargs, hooks=self.registered_hooks)
            except ImportError as e:
                logger.error("You cannot use the Websocket Postman without installing websockets")
                raise e

        else:
            raise Exception(f"Postman couldn't be configured. No Postman for type {settings.type}")

        return postman

    def getProviderFromSettings(self, transcript: Transcript):
        settings = transcript.provider

        if settings.type == ProviderProtocol.WEBSOCKET:
            try:
                from bergen.provider.websocket import WebsocketProvider
                provider = WebsocketProvider(self, **settings.kwargs, hooks=self.registered_hooks)
            except ImportError as e:
                logger.error("You cannot use the Websocket Provider without installing websockets")
                raise e

        else:
            raise Exception(f"Provider couldn't be configured. No Provider for type {settings.type}")

        return provider

    def getEntertainerFromSettings(self, transcript: Transcript):
        settings = transcript.host

        if settings.type == HostProtocol.WEBSOCKET:
            try:
                from bergen.entertainer.websocket import WebsocketEntertainer
                provider = WebsocketEntertainer(self, **settings.kwargs, hooks=self.registered_hooks)
            except ImportError as e:
                logger.error("You cannot use the Websocket Entertainer without installing websockets")
                raise e

        else:
            raise Exception(f"Entertainer couldn't be configured. No Entertainer for type {settings.type}")

        return provider
    
    async def negotiate_async(self):
        from bergen.schemas.arkitekt.mutations.negotiate import NEGOTIATION_GQL

        # Instantiate our Main Ward, this is only for Nodes and Pods
        self.main_ward = MainWard(self)
        await self.main_ward.configure()

        # We resort escalating to the different client Type protocols
        self._transcript = await NEGOTIATION_GQL.run(ward=self.main_ward, variables={"clientType": self.client_type, "internal": self.is_iternal, **self.negotiate_additionals})
 
        #Lets create our different Wards 
        
        assert self._transcript.models is not None, "We apparently didnt't get any points"
        assert self._transcript.wards is not None, "We apparently didnt't get any wards"


        ward_registry = get_ward_registry()

        ward_registry.set_base(self.main_ward)
        
        for ward in self._transcript.wards:
            ward_registry.create_ward(self, ward)

        for model in self._transcript.models:
            ward_registry.register_model(model)

        # Negotating Extensions for the Datapoints
        self._extensions = await ward_registry.configure_wards()

        self.postman = self.getPostmanFromSettings(self._transcript)
        await self.postman.connect()

        if self.client_type in [ClientType.PROVIDER, ClientType.HOST]:
            self._entertainer = self.getEntertainerFromSettings(self._transcript)
            await self._entertainer.connect()

        if self.client_type == ClientType.PROVIDER:
            self._provider = self.getProviderFromSettings(self._transcript)
            await self._provider.connect()

        self.log_table()


    def log_table(self):

        table = Table.grid()
        table.add_column()
        table.add_column()
        table.add_row()

        arkitekt_table = Table(title="Arkitekt", show_header=False)
        for key, value in self.config.dict().items():
            arkitekt_table.add_row(key,str(value))

        herre_table = Table(title="Herre", show_header=False)
        for key, value in self.auth.config.dict().items():
            if "secret" in key: continue
            herre_table.add_row(key, str(value))

        extensions_table = Table.grid()

        row = []
        for key, value in self._extensions.items():
            if isinstance(value, dict):
                extensions_table.add_column()
                sub_table = Table(title=key, show_header=False)
                for key, value in value.items():
                    sub_table.add_row(key, str(value))

                row.append(sub_table)

        extensions_table.add_row(*row)


        table.add_row("Welcome to Arnheim")
        table.add_row(herre_table, arkitekt_table)
        

        table.add_row()

        if self.client_type in [ClientType.PROVIDER, ClientType.HOST]:
            table.add_row("We are Connected as a [bold]Host[/bold]")
        if self.client_type in [ClientType.PROVIDER]:
            table.add_row("We are Connected as a [bold]Provider[/bold]")

        table.add_row()
        table.add_row("[green]Connected :pile_of_poo:")
        table.add_row(extensions_table)

        console.print(Panel(table, title="Arkitekt"))



    async def disconnect_async(self, client_type=None):
        await self.main_ward.disconnect()

        if self.postman: await self.postman.disconnect()
        if self._provider: await self._provider.disconnect()
        if self._entertainer: await self._entertainer.disconnect()

        ward_registry = get_ward_registry()
        await asyncio.gather(*[ward.disconnect() for ward in ward_registry.wards])
        print("Sucessfulyl disconnected")

    def negotiate(self):
        assert not self.loop.is_running(), "You cannot negotiate with an already running Event loop, please ue negotiate_async"
        self.loop.run_until_complete(self.negotiate_async())


    def getUser(self) -> User:
        return self.auth.getUser()

    
    def getExtensions(self, service: str) -> dict:
        """Returns the negotiated Extensions fromt he serive

        Args:
            service (str): The clearlabel Datapoint (e.g. Elements)

        Returns:
            dict: A dict of the extensions
        """
        assert self._extensions[service] is not None, "There are no extensions registered for this Service and this App (see negotiate)"
        return self._extensions[service]
    
        
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


    async def __aexit__(self, type, value, traceback):
        try:
            if value and isinstance(value, asyncio.CancelledError): 
                raise SafetyError("We caputered a Cancellation at the Bergen Context Level. Please make sure to capture it before in your code. See documentation!") from value#
        

        except Exception as e:    
            await self.disconnect_async()
            if not self.capture_exceptions: raise e


    def disconnect(self):
        self.loop.run_until_complete(self.disconnect_async())


    def __enter__(self):
        self.negotiate()
        return self

    def __exit__(self, *args, **kwargs):
        self.disconnect()


    
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

    def template(self, *args, **kwargs):
        if self._provider:
            return self.provider.template(*args, **kwargs)
        else:
            raise Exception("We are not in Provider Mode")

    async def provide_async(self):
        return await self.provider.provide_async()

    def provide(self):
        return self.provider.provide()

