
from abc import ABC, abstractmethod
from pydantic.main import BaseModel

from requests.models import Response
from bergen.enums import ClientType
import shelve
import os
import requests
import logging
from .types import User, HerreConfig
import json
logger = logging.getLogger(__name__)
from bergen.console import console


class AuthError(Exception):
    pass

class Application(BaseModel):
    name: str
    client_id: str



class BaseAuthBackend(ABC):


    def __init__(self, config: HerreConfig, token_url="o/token/", authorize_url="o/authorize/", check_endpoint="auth/", force_new_token=False) -> None:
        # Needs to be set for oauthlib
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0" if config.secure else "1"

        self.config = config
        self.base_url = f'{"https" if config.secure else "http"}://{config.host}:{config.port}/'
        self.check_url = self.base_url + check_endpoint
        self.auth_url = self.base_url + authorize_url
        self.token_url = self.base_url + token_url
        self.scopes = config.scopes + ["introspection"]
        self.client_id = config.client_id
        self.client_secret = config.client_secret  
        self.force_new_token = force_new_token  

        self.scope = " ".join(self.scopes)
        
        
        self._user = None
        self._accesstoken = None
        self._application = None

        # Lets check if we already have a local toke
        config_name = "token.db"
        run_path = os.path.abspath(os.getcwd())
        self.db_path = os.path.join(run_path, config_name)
        

        self.token = None
        self.needs_validation = False

        if not self.force_new_token:
            try:
                with shelve.open(self.db_path) as cfg:
                        self.token = cfg['token']
                        self.needs_validation = True
                        logger.debug("Found local config")
            except KeyError:
                logger.info("No configuration found")

        super().__init__()


    @abstractmethod
    def fetchToken(self, loop=None) -> str:
        raise NotImplementedError("This is an abstract Class")

    def refetchToken(self) -> str:
        raise NotImplementedError("This is an abstract Class")

    def getUser(self):
        assert self.token is not None, "Need to authenticate before accessing the User"
        if not self._user:
            answer = requests.get(self.base_url + "me/", headers={"Authorization": f"Bearer {self.access_token}"})
            self._user = User(**answer.json())
        return self._user

    @property
    def access_token(self):
        if not self._accesstoken:
            self.getToken()
        
        return self._accesstoken

    @property
    def user(self):
        if not self._user:
            self.getUser()

        return self._user

    @property
    def application(self) -> Application:
        if not self._application:
            self.getToken()

        return self._application


    def getToken(self, loop=None) -> str:
        if self._accesstoken is None:
            if self.token is None:
                try:
                    self.token = self.fetchToken()
                except:
                    logger.error(f"Couldn't fetch Token with config {self.config}")
                    raise
                
                with shelve.open(self.db_path) as cfg:
                    cfg['token'] = self.token

            response = requests.get(self.check_url, headers={"Authorization": f"Bearer {self.token['access_token']}"})



            if response.status_code != 200:
                self.token == None
                self.fetchToken()

            self._application = Application(**json.loads(response.content))
            self._accesstoken =  self.token["access_token"]

        return self._accesstoken
