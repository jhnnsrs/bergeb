from bergen.wards.graphql.subscription import SubscriptionGraphQLWard
from bergen.auths.backend_application import ArnheimBackendOauth
from bergen.clients.base import BaseBergen
from bergen.clients.mixins.querymixin import QueryMixIn
from bergen.clients.mixins.subscribemixin import SubscribeMixIn
import os

class Bergen(BaseBergen, QueryMixIn, SubscribeMixIn):

    def __init__(self, host: str = "localhost", port: int = 8000, client_id: str = None, client_secret: str = None, protocol="http", bind=True, allow_insecure=None, is_local=None, **kwargs) -> None:

        
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" if allow_insecure is not None else os.getenv("OAUTHLIB_INSECURE_TRANSPORT", "0")
        os.environ["ARNHEIM_LOCAL"] = "0" if is_local is not None else os.getenv("ARNHEIM_LOCAL", "0")


        auth = ArnheimBackendOauth(host=host, port=port, client_id=client_id, client_secret=client_secret, protocol="http", verify=True)
        main_ward = SubscriptionGraphQLWard(host=host, port=port, protocol=protocol, token=auth.getToken())

        super().__init__(auth, main_ward, auto_negotiate=True, bind=bind, **kwargs)