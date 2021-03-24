from bergen.enums import ClientType
from bergen.auths.types import GrantType
from bergen.clients.default import Bergen
import os
from bergen.auths.legacy.app import LegacyApplication
from bergen.auths.backend.app import ArnheimBackendOauth
from bergen.auths.implicit.app import ImplicitApplication


class HostBergen(Bergen):
    pass
    
    def __init__(self, *args, scopes= [],**kwargs) -> None:
        super().__init__(*args, client_type = ClientType.HOST, scopes=scopes + ["host"], **kwargs)