from bergen.wards.graphql.default import GraphQlWard
from bergen.auths.base import BaseAuthBackend
from typing import Callable
from bergen.enums import DataPointType
from bergen.clients.base import BaseWard
import logging

logger = logging.getLogger(__name__)

datapointregistry = None

class DataPointRegistry(object):


    def __init__(self) -> None:
        self.pointNameWardMap: dict[str, BaseWard] = {}
        self.builders =  {
                # Default Builders for standard
                DataPointType.GRAPHQL: lambda datapoint, auth: GraphQlWard(host=datapoint.host, port=datapoint.port, token=auth.getToken(), protocol=auth.getProtocol())
        }

    def registerClientBuilder(self, type:str , builder: Callable):
        self.builders[type] = builder

    def getClientForData(self,point, auth: BaseAuthBackend) -> BaseWard:
        if point.name in self.pointNameWardMap:
            return self.pointNameWardMap[point.name]

        logger.info("Creating new DataPoint parser")

        if point.type in self.builders:
            builder = self.builders[point.type]
            self.pointNameWardMap[point.name] = builder(point, auth)
            return self.pointNameWardMap[point.name]
        else:
            raise NotImplementedError("We have no idea how to build that datatype")






def get_datapoint_registry() -> DataPointRegistry:
    global datapointregistry
    if datapointregistry is None:
        datapointregistry = DataPointRegistry()
    return datapointregistry