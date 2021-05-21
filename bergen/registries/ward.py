from asyncio import exceptions
from bergen.schema import DataModel, DataPoint, WardSettings
from bergen.wards.default import GraphQLWard
from bergen.auths.base import BaseAuthBackend
from typing import Callable, Dict
from bergen.enums import DataPointType
import logging
import asyncio
from bergen.console import console
logger = logging.getLogger(__name__)

ward_registry = None

class WardRegistry(object):


    def __init__(self) -> None:
        self.distinctWardMap = {}
        self.distinctNegotiationMap: Dict[str, dict] = {}


        # For the Identifier on the Models
        self.identifierWardMap= {}
        self.builders =  {
                # Default Builders for standard
                DataPointType.GRAPHQL: GraphQLWard
        }

    def set_base(self, ward):
        self.identifierWardMap["node"] = ward
        self.identifierWardMap["pod"] = ward
        self.identifierWardMap["template"] = ward


    def get_ward(self, identifier):
        assert identifier in self.identifierWardMap, f"No Model registered on Identifier {identifier}"
        return self.identifierWardMap[identifier]


    def register_model(self, model: DataModel):
        assert model.point.distinct in self.distinctWardMap, "We cannot register this Model because there exists no ward for it"
        self.identifierWardMap[model.identifier] = self.distinctWardMap[model.point.distinct]

    def create_ward(self, bergen, ward_setting: WardSettings):
        logger.info(f"Creating new Ward for Datapoint {ward_setting}")

        if ward_setting.type in self.builders:
            builder = self.builders[ward_setting.type]
            self.distinctWardMap[ward_setting.distinct]  = builder(bergen, ward_setting)
        else:
            raise NotImplementedError(f"We have no idea how to build the Ward of Type {ward_setting.type}")

    async def configure_wards(self):
        wards = [ward for distinct, ward in self.distinctWardMap.items()]
        distincts = [distinct for distinct, ward in self.distinctWardMap.items()]
        negotiation_results = await asyncio.gather(*[ward.configure() for ward in wards], return_exceptions=True)
        return {distinct: result for distinct, result in zip(distincts, negotiation_results)}



def get_ward_registry() -> WardRegistry:
    global ward_registry
    if ward_registry is None:
        ward_registry = WardRegistry()
    return ward_registry