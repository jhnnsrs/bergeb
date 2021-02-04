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
        self.client_id = client_id
        self.client_secret = client_secret
        assert self.client_id is not None, "Please provide a client_id argument"
        assert self.client_secret is not None, "Please provide a client_secret argument"
        self.username = username
        self.password = password

        # Generate correct URLs
        self.base_url = f"{protocol}://{host}:{port}/o/"
        self.auth_url = self.base_url + "authorize"
        self.token_url = self.base_url + "token"

        # If you want to have a hosting QtWidget
        self.parent = parent

        self.token = None

        self.legacy_app_client =  LegacyApplicationClient(self.client_id)

        self.scopes = scopes

        super().__init__()

    def getToken(self, loop=None) -> str:
        if self.token: return self.token

        # Getting token
        if not self.username: self.username = input("Enter your username:    ")
        if not self.password: self.password = input("Password?               ")

        data = { "username": self.username, "password": self.password, "grant_type": "password", "scope": " ".join(self.scopes), "client_id": self.client_id, "client_secret": self.client_secret}

        url = self.token_url + "/"
        try:
            response = requests.post(url, data=data).json()
        except Exception as e:
            raise e


        if "access_token" in response:
            self.token = response["access_token"]
            return self.token

        else:
            raise Exception(f"Wasn't authorized! {response}")




    def getClientType(self):
        return ClientType.EXTERNAL

    def getProtocol(self):
        return "http"