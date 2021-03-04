
from abc import ABC, abstractmethod

from requests.models import Response
from bergen.enums import ClientType
import shelve
import os
import requests
import logging


logger = logging.getLogger(__name__)



class AuthError(Exception):
    pass


class BaseAuthBackend(ABC):


    def __init__(self, host, port, protocol="http", token_url="o/token", check_endpoint="auth/", scopes=None, **kwargs) -> None:

        self.base_url = f"{protocol}://{host}:{port}/"
        self.check_url = self.base_url + check_endpoint
        self.scopes = scopes + ["introspection"] if scopes else ["introspection"]
        print(self.scopes)
        self.scope = " ".join(self.scopes)

        config_name = "access.cfg"
        run_path = os.path.abspath(os.getcwd())
        self.config_path = os.path.join(run_path, config_name)

        try:
            with shelve.open(self.config_path) as cfg:
                    self.token = cfg['token']
                    self.needs_validation = True
                    logger.debug("Found local config")
        except KeyError:
            self.token = None
            self.needs_validation = False

        super().__init__()


    @abstractmethod
    def fetchToken(self, loop=None) -> str:
        raise NotImplementedError("This is an abstract Class")



    def getToken(self, loop=None) -> str:
        if self.token is None:
            self.token = self.fetchToken()
            
            with shelve.open(self.config_path) as cfg:
                cfg['token'] = self.token

            return self.token
        
        else:
            if self.needs_validation:
                response = requests.post(self.check_url, {"token": self.token}, headers={"Authorization": f"Bearer {self.token}"})
                print(response.status_code)
                self.needs_validation = False
                if response.status_code == 200:
                    logger.info("Old token still valid!")
                    return self.token
                else:
                    logger.info("Need to refetch Token!!") # Was no longer valid, fetching anew
                    self.token = self.fetchToken()

                    with shelve.open(self.config_path) as cfg:
                        cfg['token'] = self.token

                    return self.token
                
            return self.token



    @abstractmethod
    def getClientType(self) -> ClientType:
        raise NotImplementedError("This is an Abstract Class")

    @abstractmethod
    def getProtocol(self):
        raise NotImplementedError("This is an Abstract Class")