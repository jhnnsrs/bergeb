
from enum import Enum


class GrantType(str, Enum):
    IMPLICIT = "IMPLICIT"
    PASSWORD = "PASSWORD"
    BACKEND = "BACKEND"



class ClientType(str, Enum):
    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"
    USER = "USER"


class DataPointType(str, Enum):
    GRAPHQL = "GRAPHQL"
    REST = "REST"



class TYPENAMES(str, Enum):
    MODELPORTTYPE = "ModelPortType"