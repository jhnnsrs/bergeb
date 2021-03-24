from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class GrantType(str, Enum):
    IMPLICIT = "implicit"
    PASSWORD = "password"
    BACKEND = "backend"

class HerreConfig(BaseModel):
    secure: bool 
    host: str
    port: int 
    client_id: str 
    client_secret: str
    grant_type: GrantType
    scopes: List[str]
    redirect_uri: Optional[str]

    def __str__(self) -> str:
        return f"{'Secure' if self.secure else 'Insecure'} Connection to {self.host}:{self.port} on Grant {self.grant_type}"


class User(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
