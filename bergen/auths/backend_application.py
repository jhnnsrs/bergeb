
from bergen.auths.base import AuthError, BaseAuthBackend
from oauthlib.oauth2.rfc6749.clients.backend_application import BackendApplicationClient
from requests_oauthlib.oauth2_session import OAuth2Session 
from bergen.enums import ClientType
import logging
import time

logger = logging.getLogger(__name__)


class ArnheimBackendOauth(BaseAuthBackend):
    failedTries = 5
    auto_retry = True
    tokenurl_appendix = "o/token/"


    def __init__(self, host: str, port: int, client_id: str, client_secret: str, protocol="http", verify=True) -> None:
        self.host = host
        self.port = port
        self.client_id = client_id
        self.client_secret = client_secret
        self.protocol = protocol
        self.verify = verify

        self.base_url = f"{protocol}://{host}:{port}"       
        self.token_url = self.base_url + "/" + self.tokenurl_appendix
        
        super().__init__()

    def getToken(self) -> str:
        logger.info(f"Connecting to Arnheim at {self.token_url}")
        
        auth_client = BackendApplicationClient(client_id=self.client_id)
        oauth_session = OAuth2Session(client=auth_client)


        def fetch_token(thetry=0):
            try:
                return oauth_session.fetch_token(token_url=self.token_url, client_id=self.client_id,
                client_secret=self.client_secret, verify=self.verify)["access_token"]
            except Exception as e:
                if thetry == self.failedTries or not self.auto_retry: raise AuthError(f"Cannot connect to Arnheim instance on {self.token_url}: {e}")
                logger.error(f"Couldn't connect to the Arnheim Instance at {self.token_url}. Retrying in 2 Seconds")
                time.sleep(2)
                fetch_token(thetry=thetry + 1)

        return fetch_token()

    def getClientType(self) -> ClientType:
        return ClientType.EXTERNAL.value


    def getProtocol(self):
        return self.protocol