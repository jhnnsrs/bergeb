from bergen.auths.types import HerreConfig
from oauthlib.oauth2.rfc6749.clients.legacy_application import LegacyApplicationClient
from oauthlib.oauth2.rfc6749.clients.mobile_application import MobileApplicationClient
import requests
from requests_oauthlib.oauth2_session import OAuth2Session
from bergen.auths.base import BaseAuthBackend
from bergen.enums import ClientType
from bergen.console import console

class ImplicitError(Exception):
    pass


class LegacyApplication(BaseAuthBackend):


    def __init__(self, config: HerreConfig, username=None, password=None, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.username = username
        self.password = password

        self.oauth = OAuth2Session(client=LegacyApplicationClient(client_id=self.client_id))

    
    def fetchToken(self, loop=None) -> str:
        # Getting token
        self.legacy_app_client =  LegacyApplicationClient(self.client_id, scope=self.scope)
        console.print("[yellow]Try to avoid authenticating with User and Password. Use Implicit Flow if possible!")
        if not self.username: self.username = console.input("[green]Enter your [b]Username:               ")
        if not self.password: self.password = console.input("[green]Now for the [b]Password:              ", password=True)

        with console.status("[bold green]Authenticating..."):
            token = self.oauth.fetch_token(token_url=self.token_url,
            username=self.username, password=self.password, client_id=self.client_id,
            client_secret=self.client_secret)
        
        return token
