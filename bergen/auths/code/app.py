from abc import abstractmethod
from bergen.graphical import GraphicalBackend, has_webview
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib.oauth2_session import OAuth2Session
from bergen.auths.base import BaseAuthBackend
import logging

logger = logging.getLogger(__name__)

class AuthorizationCodeApplication(BaseAuthBackend):


    def __init__(self, config, parent=None, **kwargs) -> None:
        super().__init__(config , **kwargs)  
        # TESTED, just redirecting to Google works in normal browsers
        # the token string appears in the url of the address bar
        self.redirect_uri = config.redirect_uri
        assert self.redirect_uri is not None, "If you want to use the implicit flow please specifiy a redirect Uri"
        # If you want to have a hosting QtWidget
        self.parent = parent


    def fetchToken(self, loop=None) -> str:
        
        self.web_app_client = WebApplicationClient(self.client_id, scope=self.scope)

        # Create an OAuth2 session for the OSF
        self.session = OAuth2Session(
            self.client_id, 
            self.web_app_client,
            scope=self.scope, 
            redirect_uri=self.redirect_uri,
            
        )

    

        token = None

        with GraphicalBackend():
            assert has_webview, "Please install 'PyQtWebEngine' if you want to use the Implicit Flow"
            from bergen.auths.code.widgets.login import LoginDialog
            token, accepted = LoginDialog.getToken(backend=self, parent=self.parent)
            
        
        return token
        # We actually get a fully fledged thing back

