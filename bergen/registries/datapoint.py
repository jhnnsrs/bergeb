from bergen.wards.graphql.aiohttp import AIOHttpGraphQLWard
from bergen.auths.base import BaseAuthBackend
from typing import Callable, Dict
from bergen.enums import DataPointType
from bergen.clients.base import BaseWard
import logging
import asyncio
from bergen.console import console
logger = logging.getLogger(__name__)

datapointregistry = None

class DataPointRegistry(object):


    def __init__(self) -> None:
        self.pointNameWardMap: Dict[str, BaseWard] = {}
        self.builders =  {
                # Default Builders for standard
                DataPointType.GRAPHQL: lambda datapoint, bergen: AIOHttpGraphQLWard(host=datapoint.outward, port=datapoint.port, token=bergen.auth.getToken(), protocol="http", loop=bergen.loop)
        }

    def registerClientBuilder(self, type:str , builder: Callable):
        self.builders[type] = builder

    def createWardForDatapoint(self, point, bergen) -> BaseWard:
        if point.id in self.pointNameWardMap:
            return self.pointNameWardMap[point.id]

        logger.info(f"Creating new Ward for Datapoint {point}")

        if point.type in self.builders:
            builder = self.builders[point.type]
            self.pointNameWardMap[point.id]  = builder(point, bergen)
            return self.pointNameWardMap[point.id]
        else:
            raise NotImplementedError(f"We have no idea how to build the ward for this Datapoint {point.type}")

    async def configureWards(self):
        wards = [ward for point, ward in self.pointNameWardMap.items()]
        await asyncio.gather(*[ward.configure() for ward in wards])





def get_datapoint_registry() -> DataPointRegistry:
    global datapointregistry
    if datapointregistry is None:
        datapointregistry = DataPointRegistry()
    return datapointregistry