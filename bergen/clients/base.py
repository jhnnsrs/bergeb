import asyncio
from bergen.wards.graphql.aiohttp import AIOHttpGraphQLWard
from bergen.enums import ClientType
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

class BaseBergen:


    def __init__(self, auth: BaseAuthBackend, host: str, port: int, ssl=False, auto_negotiate=True, bind=True, log=logging.INFO, local=None, loop=None,  client_type: ClientType = None, jupyter=False, force_sync = False, **kwargs) -> None:
        

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
        

        try:
            self.loop = asyncio.get_running_loop()
            if self.running_in_sync:
                import nest_asyncio
                nest_asyncio.apply(self.loop)

        except RuntimeError:
            self.loop = asyncio.get_event_loop()
            self.loop_is_running = False
            logger.info("Created New Eventloop")

        if bind: 
            # We only import this here for typehints
            from bergen.registries.arnheim import set_current_arnheim
            set_current_arnheim(self)

        

        self.local = local if local is not None else os.getenv("ARNHEIM_LOCAL") == "1" 

        if self.local:
            logger.info("Running in Local Mode")

        self.client_type = client_type


        self.auth = auth
        self.token = self.auth.getToken()
        logger.info(" Auhorized!!!!!")

        self.host = host
        self.port = port
        self.protocol = "https" if ssl else "http"

        self._transcript = None
        self.identifierDataPointMap = {}
        self.identifierWardMap: dict[str, BaseWard] = {}


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
        if self._transcript is None:
            if self.running_in_sync:
                raise Exception("Not negotiated Error: Please negotiate first or set auto_negotiate=True")
            else:
                raise Exception("You are running in event Loop: Please await self.negotiate_async first or run with 'async with Bergen(....)'")

        if identifier in self.identifierWardMap:
            return self.identifierWardMap[identifier]
        else:
            return self.main_ward


    def getPostmanFromSettings(self, transcript):
        settings = transcript.postman

        if settings.type == "pika":
            try:
                from bergen.postmans.pika import PikaPostman
                postman = PikaPostman(**settings.kwargs, loop=self.loop)
            except ImportError as e:
                logger.error("You cannot use the Pika Postman without installing aio_pika")
                raise e

        elif settings.type == "websocket":
            try:
                from bergen.postmans.websocket import WebsocketPostman
                postman = WebsocketPostman(**settings.kwargs, loop=self.loop)
            except ImportError as e:
                logger.error("You cannot use the Websocket Postman without installing websockets")
                raise e

        else:
            raise Exception(f"Postman couldn't be configured. No Postman for type {settings.type}")

        return postman

    
    async def negotiate_async(self, client_type=None):
        from bergen.constants import NEGOTIATION_GQL
        from bergen.registries.datapoint import get_datapoint_registry

        # Instantiate our Main Ward, this is only for Nodes and Pods
        self.main_ward = AIOHttpGraphQLWard(host=self.host, port=self.port, protocol=self.protocol, token=self.token, loop=self.loop)
        await self.main_ward.configure()

        # We resort escalating to the different client Type protocols
        clientType = client_type or self.client_type or self.auth.getClientType()
        self._transcript = await NEGOTIATION_GQL.run_async(ward=self.main_ward, variables={"clientType": clientType, "local": self.local})
        

        #Lets create our different Wards 
        
        assert self._transcript.models is not None, "We apparently didnt't get any points"
        
        datapoint_registry = get_datapoint_registry()


        self.identifierDataPointMap = {model.identifier.lower(): model.point for model in self._transcript.models}
        self.identifierWardMap = {model.identifier.lower(): datapoint_registry.createWardForDatapoint(model.point, self) for model in self._transcript.models}

        logger.info("Succesfully registered Datapoints") 
        await datapoint_registry.configureWards()
        logger.info("Succesfully connected to Datapoints") 


        self.postman = self.getPostmanFromSettings(self._transcript)
        await self.postman.configure()

    async def disconnect_async(self, client_type=None):
        await self.postman.disconnect()

    def negotiate(self, client_type = None):
        self.loop.run_until_complete(self.negotiate_async())
        
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


