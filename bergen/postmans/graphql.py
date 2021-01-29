

import asyncio
from gql.client import AsyncClientSession
from gql.gql import gql
from gql.transport.websockets import WebsocketsTransport
from pydantic.utils import unique_list
from bergen.postmans.base import BasePostman
from aiostream import stream
from gql import Client
import logging
import uuid
from gql.transport.websockets import log as websockets_logger
websockets_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class PikaRPCClient:


    def __init__(self) -> None:
        pass



class GraphqlPostman(BasePostman):
    type = "graphql"

    def __init__(self, port= None, protocol = None, host= None, auth= None, **kwargs) -> None:
        self.token = auth["token"]
        self.port = port
        self.protocol = protocol
        self.host = host

        self.url = f"ws://{self.host}:{self.port}/graphql"
        self._headers = {"Authorization": f"Bearer: {self.token}"}
        super().__init__(**kwargs)


    async def configure(self):

        self.loop = asyncio.get_event_loop()
        self.transport =  WebsocketsTransport(url=f'ws://{self.host}:{self.port}/graphql?token={self.token}')
        self.client = Client(
        transport=self.transport, fetch_schema_from_transport=False,
        
        )

        await self.transport.connect()

        self.session = AsyncClientSession(client=self.client)



    def stream(inputs: dict, params: dict, **kwargs):
        return stream.count(interval = 0.2)


    async def assign(self, node, inputs, params, progress=False):

        assignation__subscription_gql = gql("""
        subscription Assignation($inputs: GenericScalar!, $node: NodeID!, $reference: String!, $progress: Boolean!) {
            assign(inputs: $inputs, node: $node, reference: $reference, progress: $progress){
                inputs
                outputs
                status
                statusmessage
            }
        }     
        """)
        theresult = None
        try:
            async for result in self.session.subscribe(assignation__subscription_gql, variable_values={"inputs": inputs, "node": node.id, "reference": str(uuid.uuid4()), "progress": progress}):
                if progress:
                    logger.info(str(result))
                else:
                    theresult = result
                    break
            
        except StopAsyncIteration:
            pass

        return theresult

    
    async def delay(self, node, inputs, params, client=None):

        assignation_mutation_gql = gql("""
        mutation Assignation($inputs: GenericScalar!, $node: NodeID!, $reference: String!) {
            assign(inputs: $inputs, node: $node, reference: $reference){
                inputs
                outputs
                status
                statusmessage
            }
        }     
        """)

        async with self.client as session:
            result = await session.execute(assignation_mutation_gql, variable_values={"inputs": inputs, "node": node.id, "reference": str(uuid.uuid4())})
            return result








