from bergen.clients.mixins.hostmixin import HostMixIn
from bergen.wards.graphql.subscription import SubscriptionGraphQLWard
from bergen.auths.backend_application import ArnheimBackendOauth
from bergen.clients.base import BaseArnheim
from bergen.clients.mixins.querymixin import QueryMixIn
from bergen.clients.mixins.subscribemixin import SubscribeMixIn


class ArnheimHost(BaseArnheim, QueryMixIn, SubscribeMixIn,HostMixIn ):

    def __init__(self, host: str = "localhost", port: int = 8000, client_id: str = None, client_secret: str = None, protocol="http", bind=True, log=True, name="") -> None:

        auth = ArnheimBackendOauth(host=host, port=port, client_id=client_id, client_secret=client_secret, protocol="http", verify=True)

        main_ward = SubscriptionGraphQLWard(host=host, port=port, protocol=protocol, token=auth.getToken())

        super().__init__(auth, main_ward, auto_negotiate=True, bind=bind, log=log)