
from abc import ABC, abstractmethod
from bergen.enums import ClientType


class AuthError(Exception):
    pass


class BaseAuthBackend(ABC):



    def __init__(self) -> None:
        super().__init__()


    @abstractmethod
    def getToken(self) -> str:
        raise NotImplementedError("This is an abstract Class")


    @abstractmethod
    def getClientType(self) -> ClientType:
        raise NotImplementedError("This is an Abstract Class")

    @abstractmethod
    def getProtocol(self):
        raise NotImplementedError("This is an Abstract Class")