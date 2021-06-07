
from bergen.schemas.herre.types import Application, User
from bergen.config.types import HerreConfig
import json
import logging
import os
import shelve
from abc import ABC, abstractmethod
import requests
from oauthlib.oauth2 import RefreshTokenGrant

logger = logging.getLogger(__name__)

from bergen.console import console


class AuthError(Exception):
    pass



class BaseAuthBackend(ABC):


    def __init__(self, config: HerreConfig, token_url="o/token/", authorize_url="o/authorize/", check_endpoint="auth/", force_new_token=False) -> None:
        # Needs to be set for oauthlib
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0" if config.secure else "1"
        if not config.secure: console.log("Using Insecure Oauth2 Protocol.. Please only for local and debug deployments")
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

        # Lets check if we already have a local toke
        config_name = "token.db"
        run_path = os.path.abspath(os.getcwd())
        self.db_path = os.path.join(run_path, config_name)
        self.token = None

        super().__init__()


    @abstractmethod
    def fetchToken(self, loop=None) -> str:
        raise NotImplementedError("This is an abstract Class")

    @property
    def access_token(self) -> str:        
        return self.token["access_token"]


    def refetch(self):
        """Refetches the Tokens"""
        assert self.token is not None, "Cannot refetch Token if already fetched"

        if "refresh_token" in self.token:
            result = requests.post(self.token_url, {"grant_type": "refresh_token", "refresh_token": self.token["refresh_token"], "client_id": self.client_id, "client_secret": self.client_secret})
            self.token = result.json()
            return

        self.logout()
        self.login()


    def logout(self):
        self.token = None
        with shelve.open(self.db_path) as cfg:
            cfg['token'] = None


    def login(self, force_new=False):
        try:
            with shelve.open(self.db_path) as cfg:
                self.token = cfg['token']
        except KeyError:
            pass

        if not self.token or force_new or self.force_new_token:
            try:
                self.token = self.fetchToken()
                with shelve.open(self.db_path) as cfg:
                    cfg['token'] = self.token

            except ConnectionResetError:
                raise Exception(f"We couldn't connect to the Herre instance at {self.base_url}")     
            except:
                raise

        # Checking connection
        print("Reached here")
        response = requests.get(self.check_url, headers={"Authorization": f"Bearer {self.token['access_token']}"})

        if response.status_code != 200:
            # Our Initial Token was wrong, lets try to get a new one
            self.token = self.fetchToken()
            response = requests.get(self.check_url, headers={"Authorization": f"Bearer {self.token['access_token']}"})

        assert response.status_code == 200, "Was not able to get a valid token"


    def getToken(self, loop=None, force=False) -> str:
        if self._accesstoken is None:
            if force or self.token is None or self.force_new_token:

                try:
                    self.token = self.fetchToken()
                except ConnectionResetError:
                    raise Exception(f"We couldn't connect to the Herre instance at {self.base_url}")     
                except:
                    logger.error(f"Couldn't fetch Token with config {self.config}")
                    raise
                

                with shelve.open(self.db_path) as cfg:
                    cfg['token'] = self.token

            # Checking connection
            response = requests.get(self.check_url, headers={"Authorization": f"Bearer {self.token['access_token']}"})

            if response.status_code != 200:
                self.token = self.fetchToken()
                response = requests.get(self.check_url, headers={"Authorization": f"Bearer {self.token['access_token']}"})


            assert response.status_code == 200, "Was not able to get a valid token"

            self._application = Application(**json.loads(response.content))

            print(self.token)
            self._accesstoken = self.token["access_token"]
            self._refresh_token = self.token["refresh_token"] if "refresh_token" in self.token else None

        return self._accesstoken
