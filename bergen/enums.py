
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


class DataPointType(str, Enum):
    GRAPHQL = "GRAPHQL"
    REST = "REST"



class TYPENAMES(str, Enum):
    MODELPORTTYPE = "ModelPortType"