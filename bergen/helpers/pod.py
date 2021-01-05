from abc import ABC
from bergen.constants import END_GQL, MARK_GQL, YIELD_GQL
from bergen.schema import Volunteer, Assignation, AssignationStatus
import logging


logger = logging.getLogger(__name__)

class PodHelper(ABC):
    ''' This helps your pod do access the arnheim instance '''


    def __init__(self, volunteer: Volunteer, assignation: Assignation, arnheim):
        self.volunteer = volunteer
        self.assignation = assignation
        self.arnheim = arnheim


    def update(self, message, level=logging.DEBUG):
        if level == logging.DEBUG:
            MARK_GQL.run(ward=self.arnheim.main_ward, variables={"message": message, "assignation": self.assignation.id, "level": AssignationStatus.PROGRESS})
        else:
            return

    def end(self, outputs: dict):
        return END_GQL.run(ward=self.arnheim.main_ward, variables={"outputs": outputs, "assignation": self.assignation.id})

    def nudge(self, outputs: dict):
        return YIELD_GQL.run(ward=self.arnheim.main_ward, variables={"outputs": outputs, "assignation": self.assignation.id})

    def critical(self, message):
        return MARK_GQL.run(ward=self.arnheim.main_ward, variables={"message": message, "assignation": self.assignation.id, "level": AssignationStatus.CRITICAL})


