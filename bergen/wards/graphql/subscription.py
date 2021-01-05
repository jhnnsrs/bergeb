from bergen.wards.graphql.base import QueryException
from bergen.query import TypedGQL
import json
from bergen.wards.graphql.default import GraphQlWard
import logging
import websockets
import uuid

logger = logging.getLogger(__name__)

class SubscriptionGraphQLWard(GraphQlWard):
    subprotocols = ["graphql-ws"]
    extra_headers = {}
    can_subscribe = True

    def __init__(self, port=8000, host="localhost", protocol="http", token=None) -> None:
        self._websocket_endpoint = f"ws://{host}:{port}/graphql?token={token}" 
        super().__init__(port=port, host=host, protocol=protocol, token=token)


    def build_ws_message(self, type, payload = None, id = None):
        message = {"type": type, "payload": payload or {}}
        if id: message.update({"id":id})
        return json.dumps(message)


    async def subscribe(self,gql: TypedGQL, variables: dict, extract=True):
        logger.info(f"Starting Subscription for: {gql.operation_name}")
        async with websockets.connect(self._websocket_endpoint, subprotocols=self.subprotocols, extra_headers=self.extra_headers) as websocket:
            await websocket.send(self.build_ws_message("connection_init"))

            id = str(uuid.uuid4())
            payload = gql.combine(variables=variables)
            await websocket.send(self.build_ws_message("start", payload=payload, id=id))

            while True:
                signal = await websocket.recv()
                answer = json.loads(signal)
                type = answer["type"]
                if type == "ka": pass # We received a keep alive signal
                if type == "complete": break
                if type == "data":
                    payload = answer["payload"]
                    if "errors" in payload: raise QueryException(f'Error in Payload: {payload["errors"]}')
                    test = gql.extract(payload)
                    yield gql.cls(**test)