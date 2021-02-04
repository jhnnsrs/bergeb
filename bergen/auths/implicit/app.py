from abc import abstractmethod
from urllib.parse import non_hierarchical

from oauthlib.oauth2.rfc6749.clients.mobile_application import MobileApplicationClient
from requests_oauthlib.oauth2_session import OAuth2Session
from bergen.auths.base import AuthError, BaseAuthBackend
from bergen.enums import ClientType
import logging

logger = logging.getLogger(__name__)

try:
    from bergen.auths.implicit.widgets.login import LoginDialog
    # this has to be here because QtWebENgineWIdgets must be imported before a QCore Application
    Dialog = LoginDialog

except Exception as e:
    logger.debug(e)
    Dialog = None


class ImplicitApplication(BaseAuthBackend):


    def __init__(self, client_id = None, redirect_uri = "http://localhost:3000/callback", host="localhost", port= 8000, protocol = "http", scopes= ["read"], parent=None, **kwargs) -> None:
        self.client_id = client_id
        assert self.client_id is not None, "Please provide a client_id argument"
        # TESTED, just redirecting to Google works in normal browsers
        # the token string appears in the url of the address bar
        self.redirect_uri = redirect_uri

        # Generate correct URLs
        self.base_url = f"{protocol}://{host}:{port}/o/"
        self.auth_url = self.base_url + "authorize"
        self.token_url = self.base_url + "token"

        # If you want to have a hosting QtWidget
        self.parent = parent

        self.token = None


        self.mobile_app_client = MobileApplicationClient(client_id)

        # Create an OAuth2 session for the OSF
        self.session = OAuth2Session(
            client_id, 
            self.mobile_app_client,
            scope=" ".join(scopes), 
            redirect_uri=self.redirect_uri,
        )


        super().__init__()

    def getToken(self, loop=None) -> str:

        try:
            if not self.token:
                token, result = Dialog.getToken(backend=self, parent=self.parent)
                if result:
                    self.token = token
                else:
                    raise AuthError("Couldn't return a proper token")

        except Exception as e:
            raise NotImplementedError("It appears that you have not Installed PyQt5")
        
        return self.token["access_token"] # We actually get a fully fledged thing back


    def getClientType(self):
        return ClientType.EXTERNAL

    def getProtocol(self):
        return "http"