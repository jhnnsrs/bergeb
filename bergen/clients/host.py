from bergen.enums import ClientType
from bergen.clients.default import Bergen


class HostBergen(Bergen):
    pass
    
    def __init__(self, *args, scopes= [],**kwargs) -> None:
        super().__init__(*args, client_type = ClientType.HOST, scopes=scopes + ["host"], **kwargs)