from pydantic.main import BaseModel


class User(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str


class Application(BaseModel):
    name: str
    client_id: str

