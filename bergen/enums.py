
from enum import Enum

class HostProtocol(str, Enum):
    WEBSOCKET = "WEBSOCKET"

class ProviderProtocol(str, Enum):
    WEBSOCKET = "WEBSOCKET"

class PostmanProtocol(str, Enum):
    WEBSOCKET = "WEBSOCKET"
    KAFKA = "KAFKA"
    RABBITMQ = "RABBITMQ"

class ClientType(str, Enum):
    HOST = "HOST"
    CLIENT = "CLIENT"
    PROVIDER = "PROVIDER"
    POINT = "POINT"


class DataPointType(str, Enum):
    GRAPHQL = "GRAPHQL"
    REST = "REST"



class PortTypes(str, Enum):
    MODEL_ARG_PORT = "ModelArgPort"
    MODEL_KWARG_PORT = "ModelKwargPort"
    MODEL_RETURN_PORT = "ModelReturnPort"