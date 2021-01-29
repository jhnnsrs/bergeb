from bergen.queries.delayed.template import TEMPLATE_GET_QUERY
from bergen.extenders.port import PortExtender
from bergen.types.object import ArnheimObject
from bergen.types.model import ArnheimModel
from bergen.delayed import CREATE_NODE_MUTATION, NODE_FILTER_QUERY, NODE_QUERY
from enum import Enum
from typing import  Any, Generic, List, Optional, Type, TypeVar
try:
	# python 3.8
	from typing import ForwardRef
except ImportError:
	# ForwardRef is private in python 3.6 and 3.7
	from typing import _ForwardRef as ForwardRef

User = ForwardRef("User")
DataModel = ForwardRef("DataModel")



class AssignationParams(ArnheimObject):
    provider: Optional[str]




class Avatar(ArnheimObject):
    user: Optional['User']
    avatar: Optional[str]

class User(ArnheimModel):
    id: Optional[int]
    username: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    avatar: Optional[Avatar]

    class Meta:
        identifier = "user"

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


class PostmanArgs(ArnheimObject):
    type: Optional[str]
    kwargs: Optional[dict]


class Transcript(ArnheimObject):
    array: Optional[Any]
    extensions: Optional[Any]
    postman: Optional[PostmanArgs]
    models: Optional[List[DataModel]]
    points: Optional[List[DataPoint]]
    user: Optional[User]


class Port(PortExtender, ArnheimObject):
    required: Optional[bool]
    key: Optional[str]
    identifier: Optional[str] # Only for our friends the Models


class Node(ArnheimModel):
    id: Optional[int]
    name: Optional[str]
    package: Optional[str]
    inputs: Optional[List[Port]]
    outputs: Optional[List[Port]]


    class Meta:
        identifier = "node"



class ArnheimApplication(ArnheimModel):
    logo: Optional[str]

    class Meta:
        identifier = "arnheim_application"


class Peasent(ArnheimModel):
    name: Optional[str]
    application: Optional[ArnheimApplication]

    class Meta:
        identifier = "peasent"


class Volunteer(ArnheimModel):
    identifier: str
    node: Node

    class Meta:
        identifier = "volunteer"

class Template(ArnheimModel):
    node: Optional[Node]

    class Meta:
        identifier = "template"
        get = TEMPLATE_GET_QUERY


class PeasentTemplate(Template):

    class Meta:
        identifier = "peasenttemplate"




class Pod(ArnheimModel):
    template: Optional[Template]
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
