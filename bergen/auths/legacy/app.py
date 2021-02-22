from oauthlib.oauth2.rfc6749.clients.legacy_application import LegacyApplicationClient
from oauthlib.oauth2.rfc6749.clients.mobile_application import MobileApplicationClient
import requests
from requests_oauthlib.oauth2_session import OAuth2Session
from bergen.auths.base import BaseAuthBackend
from bergen.enums import ClientType

class ImplicitError(Exception):
    pass


class LegacyApplication(BaseAuthBackend):


    def __init__(self, client_id = None, client_secret=None, username=None, password=None, host="localhost", port= 8000, protocol = "http", scopes= ["read"], parent=None, **kwargs) -> None:
        assert client_id is not None, "Please provide a client_id argument"
        assert client_secret is not None, "Please provide a client_secret argument"
        super().__init__(host, port, protocol=protocol, scopes=scopes)

        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = self.base_url + "o/authorize"
        self.token_url = self.base_url + "o/token"

        # If you want to have a hosting QtWidget
        self.parent = parent
        self.legacy_app_client =  LegacyApplicationClient(self.client_id)
        self.scopes = scopes

        

    def fetchToken(self, loop=None) -> str:
        # Getting token
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


    def getClientType(self):
        return ClientType.EXTERNAL

    def getProtocol(self):
        return "http"