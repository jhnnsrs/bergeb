from abc import abstractmethod
from bergen.auths.types import HerreConfig

from oauthlib.oauth2.rfc6749.clients.mobile_application import MobileApplicationClient
from requests_oauthlib.oauth2_session import OAuth2Session
from bergen.auths.base import BaseAuthBackend
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


    def __init__(self, config: HerreConfig, parent=None, **kwargs) -> None:
        super().__init__(config , **kwargs)  
        # TESTED, just redirecting to Google works in normal browsers
        # the token string appears in the url of the address bar
        self.redirect_uri = config.redirect_uri
        assert self.redirect_uri is not None, "If you want to use the implicit flow please specifiy a redirect Uri"
        # If you want to have a hosting QtWidget
        self.parent = parent


    def fetchToken(self, loop=None) -> str:
        
        self.mobile_app_client = MobileApplicationClient(self.client_id, scope=self.scope)

        # Create an OAuth2 session for the OSF
        self.session = OAuth2Session(
            self.client_id, 
            self.mobile_app_client,
            scope=self.scope, 
            redirect_uri=self.redirect_uri,
        )

        try:
            token, result = Dialog.getToken(backend=self, parent=self.parent)
            return token["access_token"]    

        except Exception as e:
            raise NotImplementedError("It appears that you have not Installed PyQt5")
        # We actually get a fully fledged thing back

