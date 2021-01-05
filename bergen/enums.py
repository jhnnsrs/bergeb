
from enum import Enum

class ClientType(str, Enum):
    EXTERNAL = "EXTERNAL"
    USER = "USER"


class DataPointType(str, Enum):
    GRAPHQL = "GRAPHQL"
    REST = "REST"



class TYPENAMES(str, Enum):
    MODELPORTTYPE = "ModelPortType"