from typing import Dict
from bergen.schemas.arkitekt.mutations.host import HOST_GQL
from bergen.schema import DataModel
from bergen.enums import ClientType, DataPointType
from bergen.clients.default import Bergen


class PointBergen(Bergen):

    def __init__(self, *args, point_inward=None, point_outward=None, point_port=None, point_type = DataPointType.GRAPHQL, scopes= [], needs_negotiation=False, **kwargs) -> None:
        super().__init__(*args, client_type = ClientType.POINT, scopes=scopes + ["host","provide"], **kwargs)
        self.model_registry: Dict[str, DataModel] = {}
        self.negotiate_additionals = {
            "inward": point_inward,
            "outward": point_outward,
            "port": point_port,
            "pointType": point_type.value,
            "needsNegotiation": needs_negotiation,
        }


    def register(self, model: DataModel):
        self.model_registry[model.identifier] = model


    def start(self):
        self.negotiate()

        params = []
        for model in self.model_registry.values():
            params = {"identifier": model.identifier, "extenders": model.extenders}
            HOST_GQL.run(ward=self.main_ward, variables=params)

        

     
