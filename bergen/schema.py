from bergen.types.node.inputs import Inputs, Outputs
from bergen.types.manager import ModelManager
from bergen.extenders.node import NodeExtender
from bergen.extenders.user import UserPrettifier
from bergen.extenders.port import PortExtender
from bergen.types.object import ArnheimObject
from bergen.types.model import ArnheimModel
from bergen.delayed import CREATE_NODE_MUTATION, NODE_FILTER_QUERY, NODE_QUERY
from enum import Enum
from typing import  Any, ForwardRef, Generic, List, Optional, Type, TypeVar


Node = ForwardRef("Node")
User = ForwardRef("User")
DataModel = ForwardRef("DataModel")

class Avatar(ArnheimObject):
    user: Optional['User']
    avatar: Optional[str]



class User(UserPrettifier, ArnheimModel):
    id: Optional[int]
    username: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    avatar: Optional[Avatar]

    class Meta:
        identifier = "user"
        get = NODE_QUERY



class DataPoint(ArnheimModel):
    type: Optional[str]
    name: Optional[str]
    host: Optional[str]
    port: Optional[int]
    url: Optional[str]
    models: Optional[List[DataModel]]

    class Meta:
        identifier = "datapoint"


class DataModel(ArnheimModel):
    identifier: Optional[str]
    extenders: Optional[List[str]]
    point: Optional[DataPoint]

    class Meta:
        identifier = "datamodel"


class Transcript(ArnheimObject):
    array: Optional[Any]
    extensions: Optional[Any]
    models: Optional[List[DataModel]]
    points: Optional[List[DataPoint]]
    user: Optional[User]


class PortType(PortExtender, ArnheimObject):
    required: Optional[bool]
    key: Optional[str]
    identifier: Optional[str] # Only for our friends the Models


class NodeManager(ModelManager['Node']):


    def get(self, ward=None, **kwargs) -> 'Node':
        return NODE_QUERY(self.model).run(ward=ward, variables=kwargs)


    def get_or_create(self, inputs: Type[Inputs] = None, outputs: Type[Outputs] = None , **kwargs) -> 'Node':
        
        parsed_inputs = inputs.serialized
        parsed_outputs = outputs.serialized
        
        node = CREATE_NODE_MUTATION(self.model).run(variables={
            "inputs" : parsed_inputs,
            "outputs": parsed_outputs,
            **kwargs

        })
        return node



class Node(NodeExtender, ArnheimModel):
    __slots__ = ("_pod","_provisionhandler")


    id: Optional[int]
    name: Optional[str]
    package: Optional[str]
    inputs: Optional[List[PortType]]
    outputs: Optional[List[PortType]]

    objects = NodeManager()

    class Meta:
        identifier = "node"
        filter = NODE_FILTER_QUERY


class Volunteer(ArnheimModel):
    id: int
    identifier: str
    node: Node

    class Meta:
        identifier = "volunteer"

class Template(ArnheimModel):
    node: Optional[Node]

    class Meta:
        identifier = "template"


class Pod(ArnheimModel):
    template: Optional[Template]
    id: int
    status: Optional[str]

    class Meta:
        identifier = "pod"


class Provision(ArnheimModel):
    pod: Optional[Pod]
    node: Optional[Node]
    status: Optional[str]
    statusmessage: Optional[str]
    reference: Optional[str]

    class Meta:
        identifier = "provision"


class AssignationStatus(str, Enum):
    ERROR = "ERROR"
    PROGRESS = "PROGRESS"
    DEBUG = "DEBUG"
    DONE = "DONE"
    CRITICAL ="CRITICAL"
    PENDING = "PENDING"


class ProvisionStatus(str, Enum):
    ERROR = "ERROR"
    PROGRESS = "PROGRESS"
    DEBUG = "DEBUG"
    ASSIGNED = "ASSIGNED"
    CRITICAL ="CRITICAL"
    PENDING = "PENDING"

class PodStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    ERROR = "ERROR"

class Assignation(ArnheimModel):
    pod: Optional[Pod]
    id: Optional[int]
    inputs: Optional[dict]
    outputs: Optional[dict]
    message: Optional[str]
    status: Optional[str]
    statusmessage: Optional[str]

    class Meta:
        identifier = "assignation"


class VartPod(Pod):
    volunteer:  Optional[Volunteer] 

    class Meta:
        identifier = "vartpod"




Avatar.update_forward_refs()
DataPoint.update_forward_refs()
Node.update_forward_refs()
