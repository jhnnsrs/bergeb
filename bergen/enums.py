
from enum import Enum


class GrantType(str, Enum):
    IMPLICIT = "IMPLICIT"
    PASSWORD = "PASSWORD"
    BACKEND = "BACKEND"


class PostmanProtocol(str, Enum):
    WEBSOCKET = "WEBSOCKET"
    KAFKA = "KAFKA"
    RABBITMQ = "RABBITMQ"

class ClientType(str, Enum):
    HOST = "HOST"
    CLIENT = "CLIENT"


class DataPointType(str, Enum):
    GRAPHQL = "GRAPHQL"
    REST = "REST"



class TYPENAMES(str, Enum):
    MODELPORTTYPE = "ModelPortType"