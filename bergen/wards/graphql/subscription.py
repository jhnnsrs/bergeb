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

    def __init__(self, port=8000, host="localhost", protocol="http", token=None, loop=None) -> None:
        self._websocket_endpoint = f"ws://{host}:{port}/graphql?token={token}" 
        super().__init__(port=port, host=host, protocol=protocol, token=token, loop=loop)

