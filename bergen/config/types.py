from enum import Enum
from typing import List, Optional
from pydantic.main import BaseModel


class ArkitektConfig(BaseModel):
    secure: bool
    host: str
    port: int
    internal: bool = False

    def __str__(self) -> str:
        return f"{'Internal' if self.internal else 'Public'} {'Secure' if self.secure else 'Insecure'} Connection to Arkitekt on {self.host}:{self.port}"


class GrantType(str, Enum):
    IMPLICIT = "IMPLICIT"
    PASSWORD = "PASSWORD"
    CLIENT_CREDENTIALS = "CLIENT_CREDENTIALS"
    AUHORIZATION_CODE = "AUTHORIZATION_CODE"

class HerreConfig(BaseModel):
    secure: bool 
    host: str
    port: int 
    client_id: str 
    client_secret: str
    authorization_grant_type: GrantType
    scopes: List[str]
    redirect_uri: Optional[str]

    def __str__(self) -> str:
        return f"{'Secure' if self.secure else 'Insecure'} Connection to {self.host}:{self.port} on Grant {self.authorization_grant_type}"
