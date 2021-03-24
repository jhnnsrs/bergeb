from bergen.enums import ClientType
from bergen.clients.default import Bergen


class ProviderBergen(Bergen):

    def __init__(self, *args, scopes= [],**kwargs) -> None:
        super().__init__(*args, client_type = ClientType.PROVIDER, scopes=scopes + ["host","provide"], **kwargs)

     
