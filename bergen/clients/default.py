from bergen.postmans.pika import PikaPostman
from bergen.auths.legacy.app import LegacyApplication
from bergen.auths.backend.app import ArnheimBackendOauth
from bergen.auths.implicit.app import ImplicitApplication
from bergen.wards.graphql.subscription import SubscriptionGraphQLWard
from bergen.clients.base import BaseBergen
from bergen.enums import GrantType
from bergen.clients.mixins.querymixin import QueryMixIn
from bergen.clients.mixins.subscribemixin import SubscribeMixIn
import os

class Bergen(BaseBergen, QueryMixIn, SubscribeMixIn):

    def __init__(self, 
    host: str = "localhost", 
    port: int = 8000,
    client_id: str = None, 
    client_secret: str = None,
    grant_type: GrantType = GrantType.BACKEND,
    protocol="http", bind=True,
    allow_insecure=None,
    is_local=None,
    **kwargs) -> None:

        
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" if allow_insecure is not None else os.getenv("OAUTHLIB_INSECURE_TRANSPORT", "0")
        os.environ["ARNHEIM_LOCAL"] = "0" if is_local is not None else os.getenv("ARNHEIM_LOCAL", "0")


        if grant_type == GrantType.BACKEND: auth = ArnheimBackendOauth(host=host, port=port, client_id=client_id, client_secret=client_secret, protocol="http", verify=True, **kwargs)
        elif grant_type == GrantType.IMPLICIT: auth = ImplicitApplication(host=host, port=port, client_id=client_id, client_secret=client_secret, protocol="http", verify=True, **kwargs)
        elif grant_type == GrantType.PASSWORD: auth = LegacyApplication(host=host, port=port, client_id=client_id, client_secret=client_secret, protocol="http", verify=True, **kwargs)
        else: raise NotImplementedError("Please Specifiy a valid Grant Type")

        super().__init__(auth, host, port, protocol = protocol, auto_negotiate=True, bind=bind, **kwargs)