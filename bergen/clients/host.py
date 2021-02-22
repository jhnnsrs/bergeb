from bergen.clients.base import BaseBergen
from bergen.enums import GrantType
from bergen.clients.default import Bergen
from bergen.peasent.websocket import WebsocketPeasent
import os
from bergen.auths.legacy.app import LegacyApplication
from bergen.auths.backend.app import ArnheimBackendOauth
from bergen.auths.implicit.app import ImplicitApplication


class HostBergen(WebsocketPeasent, BaseBergen):


     def __init__(self, 
    host: str = None, 
    port: int = None,
    client_id: str = None, 
    client_secret: str = None,
    grant_type: GrantType = GrantType.BACKEND,
    protocol="http", bind=True,
    allow_insecure=None,
    is_local=None,
    **kwargs) -> None:

        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" if allow_insecure is not None else os.getenv("OAUTHLIB_INSECURE_TRANSPORT", "0")
        os.environ["ARNHEIM_LOCAL"] = "0" if is_local is not None else os.getenv("ARNHEIM_LOCAL", "0")

        protocol = protocol or os.getenv("ARNHEIM_PROTOCOL", "http")
        host = host or os.getenv("ARNHEIM_HOST", "localhost")
        port = int(port or os.getenv("ARNHEIM_PORT", "8000"))
        client_id = client_id or os.getenv("ARNHEIM_CLIENT_ID", None)
        client_secret = client_secret or os.getenv("ARNHEIM_CLIENT_SECRET", None)
        grant_type = grant_type or os.getenv("ARNHEIM_GRANT_TYPE", GrantType.BACKEND)

        if grant_type == GrantType.BACKEND: auth = ArnheimBackendOauth(host=host, port=port, client_id=client_id, client_secret=client_secret, protocol=protocol, verify=True, **kwargs)
        elif grant_type == GrantType.IMPLICIT: auth = ImplicitApplication(host=host, port=port, client_id=client_id, client_secret=client_secret, protocol=protocol, verify=True, **kwargs)
        elif grant_type == GrantType.PASSWORD: auth = LegacyApplication(host=host, port=port, client_id=client_id, client_secret=client_secret, protocol=protocol, verify=True, **kwargs)
        else: raise NotImplementedError("Please Specifiy a valid Grant Type")

        super().__init__(auth=auth, host=host, port=port, protocol = protocol, auto_negotiate=True, bind=bind, **kwargs)
