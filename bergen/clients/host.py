from bergen.enums import GrantType
from bergen.clients.mixins.hostmixin import HostMixIn
from bergen.wards.graphql.subscription import SubscriptionGraphQLWard
from bergen.auths.backend.app import ArnheimBackendOauth
from bergen.clients.base import BaseBergen
from bergen.clients.mixins.querymixin import QueryMixIn
from bergen.clients.mixins.subscribemixin import SubscribeMixIn


class BergenHost(BaseBergen, QueryMixIn, SubscribeMixIn, HostMixIn ):

    def __init__(self, host: str = "localhost", port: int = 8000, client_id: str = None, client_secret: str = None, protocol="http", bind=True, log=True, name="", grant_type: GrantType = GrantType.BACKEND) -> None:

        auth = ArnheimBackendOauth(host=host, port=port, client_id=client_id, client_secret=client_secret, protocol="http", verify=True)

        main_ward = SubscriptionGraphQLWard(host=host, port=port, protocol=protocol, token=auth.getToken())

        super().__init__(auth, main_ward, auto_negotiate=True, bind=bind, log=log)