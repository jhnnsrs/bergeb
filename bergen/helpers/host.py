from abc import ABC
from bergen.constants import VOLUNTEER_GQL
import logging
from typing import Callable
from bergen.schema import Volunteer, Pod, Node


logger = logging.getLogger(__name__)


class HostHelper(ABC):


    def __init__(self, arnheim) -> None:
        self.arnheim = arnheim
        self.identifierFunctionMap: dict[str, Callable] = {}
        self.identifierVolunteerMap: dict[str, Volunteer] = {}
        self.identifierPodMap: dict[str, Pod] = {}
        self.podIDIdentifierMap: dict[int, str] = {}

    def addVolunteer(self, volunteer: Volunteer):
        self.identifierVolunteerMap[volunteer.identifier] = volunteer
        logger.info(f"Successfully added Volunteer for {volunteer.node.name}: VolunteerID: {volunteer.id}")

    def addPod(self, pod: Pod):
        self.identifierPodMap[pod.volunteer.identifier] = pod
        self.podIDIdentifierMap[pod.id] = pod.volunteer.identifier
        logger.info(f"Successfully added Pod for {pod.id}")


    def addVolunteerFunction(self, volunteer: Volunteer, callable: Callable):
        self.identifierFunctionMap[volunteer.identifier] = callable


    def getFunctionForPod(self, pod: Pod):
        return self.identifierFunctionMap[self.getIdentifierForPod(pod)]

    def getVolunteers(self):
        return [volunteer for key, volunteer in self.identifierVolunteerMap.items()]
        
    def volunteer(self, node: Node, version="standard"):
        # Implement getting node
        volunteer = VOLUNTEER_GQL.run(ward=self.arnheim.main_ward, variables = {"nodeid": node.id, "name": self.arnheim.name, "version": version})
        self.addVolunteer(volunteer)
        return volunteer


    def getIdentifierForPod(self, pod: Pod):
        return self.podIDIdentifierMap[pod.id]

    def getPodForIdentifier(self, identifier):
        return self.identifierPodMap[identifier]

    def getVolunteerForPod(self, pod: Pod):
        return self.identifierVolunteerMap[self.getIdentifierForPod(pod)]