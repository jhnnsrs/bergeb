import logging
import time

from bergen.auths.base import  BaseAuthBackend
from bergen.console import console
from oauthlib.oauth2.rfc6749.clients.backend_application import \
    BackendApplicationClient
from requests_oauthlib.oauth2_session import OAuth2Session

logger = logging.getLogger(__name__)


class ArnheimBackendOauth(BaseAuthBackend):

    def __init__(self, config, **kwargs) -> None:
        super().__init__(config , **kwargs)  

    def fetchToken(self, loop=None) -> str:
        # Connecting
        
        with console.status("[bold green]Authenticating..."):
            auth_client = BackendApplicationClient(client_id=self.client_id, scope=self.scope)
            oauth_session = OAuth2Session(client=auth_client, scope=self.scope)

            token = oauth_session.fetch_token(token_url=self.token_url, client_id=self.client_id,
            client_secret=self.client_secret, verify=True)

        return token
                
