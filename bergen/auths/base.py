
from abc import ABC, abstractmethod

from requests.models import Response
from bergen.enums import ClientType
import shelve
import os
import requests
import logging
from .types import User, HerreConfig

logger = logging.getLogger(__name__)



class AuthError(Exception):
    pass





class BaseAuthBackend(ABC):


    def __init__(self, config: HerreConfig, token_url="o/token/", authorize_url="o/authorize/", check_endpoint="auth/") -> None:
        # Needs to be set for oauthlib
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0" if config.secure else "1"



        self.base_url = f'{"https" if config.secure else "http"}://{config.host}:{config.port}/'
        self.check_url = self.base_url + check_endpoint
        self.auth_url = self.base_url + authorize_url
        self.token_url = self.base_url + token_url
        self.scopes = config.scopes + ["introspection"]
        self.client_id = config.client_id
        self.client_secret = config.client_secret  

        self.scope = " ".join(self.scopes)
        self._user = None

        # Lets check if we already have a local toke
        config_name = "token.db"
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

    def refetchToken(self) -> str:
        raise NotImplementedError("This is an abstract Class")

    def getUser(self):
        assert self.token is not None, "Need to authenticate before accessing the User"
        if not self._user:
            answer = requests.get(self.base_url + "me", headers={"Authorization": f"Bearer {self.token}"})
            self._user = User(**answer.json())
        return self._user

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
