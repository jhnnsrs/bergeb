from bergen.auths.types import HerreConfig
from oauthlib.oauth2.rfc6749.clients.legacy_application import LegacyApplicationClient
from oauthlib.oauth2.rfc6749.clients.mobile_application import MobileApplicationClient
import requests
from requests_oauthlib.oauth2_session import OAuth2Session
from bergen.auths.base import BaseAuthBackend
from bergen.enums import ClientType

class ImplicitError(Exception):
    pass


class LegacyApplication(BaseAuthBackend):


    def __init__(self, config: HerreConfig, username=None, password=None, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.username = username
        self.password = password

    
    def fetchToken(self, loop=None) -> str:
        # Getting token

        self.legacy_app_client =  LegacyApplicationClient(self.client_id)
        if not self.username: self.username = input("Enter your username:    ")
        if not self.password: self.password = input("Password?               ")

        data = { "username": self.username, "password": self.password, "grant_type": "password", "scope": self.scope, "client_id": self.client_id, "client_secret": self.client_secret}

        url = self.token_url + "/"
        try:
            response = requests.post(url, data=data).json()
        except Exception as e:
            raise e


        if "access_token" in response:
            return response["access_token"]
        else:
            raise Exception(f"Wasn't authorized! {response}")
