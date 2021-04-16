from bergen.enums import HostProtocol, PostmanProtocol, ProviderProtocol
from bergen.queries.delayed.pod import POD_QUERY
from bergen.queries.delayed.template import TEMPLATE_GET_QUERY
from bergen.extenders.port import ArgPortExtender, KwargPortExtender, ReturnPortExtender
from bergen.types.object import ArnheimObject
from bergen.types.model import ArnheimModel
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

class ProvisionParams(ArnheimObject):
    provider: Optional[str]
    auto_unprovide: Optional[bool]

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
    inward: Optional[str]
    outward: Optional[str]
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



class PostmanSettings(ArnheimObject):
    type: Optional[PostmanProtocol]
    kwargs: Optional[dict]

class ProviderSettings(ArnheimObject):
    type: Optional[ProviderProtocol]
    kwargs: Optional[dict]

class EntertainerSettings(ArnheimObject):
    type: Optional[HostProtocol]
    kwargs: Optional[dict]

class Transcript(ArnheimObject):
    extensions: Optional[Any]
    postman: Optional[PostmanSettings]
    host: Optional[EntertainerSettings]
    provider: Optional[ProviderSettings]
    models: Optional[List[DataModel]]


class Provider(ArnheimModel):
    name: Optional[str]

    class Meta:
        identifier = "provider"


class Widget(ArnheimObject):
    query: Optional[str]
    dependencies: Optional[List[str]]


class ArgPort(ArgPortExtender, ArnheimObject):
    __slots__ = ("_widget", )

    required: Optional[bool]
    key: Optional[str]
    identifier: Optional[str] 
    label: Optional[str]
    widget: Optional[Widget]

class KwargPort(KwargPortExtender, ArnheimObject):
    __slots__ = ("_widget", )

    required: Optional[bool]
    key: Optional[str]
    identifier: Optional[str] 
    label: Optional[str]
    default: Optional[Any]
    widget: Optional[Widget]

class ReturnPort(ReturnPortExtender, ArnheimObject):
    __slots__ = ("_widget", )

    required: Optional[bool]
    key: Optional[str]
    identifier: Optional[str] 
    label: Optional[str]


class NodeType(str, Enum):
    FUNCTION = "FUNCTION"
    GENERATOR = "GENERATOR"


class Node(ArnheimModel):
    id: Optional[int]
    name: Optional[str]
    package: Optional[str]
    interface: Optional[str]
    args: Optional[List[ArgPort]]
    kwargs: Optional[List[KwargPort]]
    returns: Optional[List[ReturnPort]]
    type: Optional[NodeType]


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
    provider: Optional[Provider]
    channel: Optional[str]

    class Meta:
        identifier = "template"
        get = TEMPLATE_GET_QUERY



class Pod(ArnheimModel):
    name: Optional[str]
    channel: Optional[str]
    template: Optional[Template]
    status: Optional[str]

    class Meta:
        identifier = "pod"

class PeasentPod(Pod):
    peasent: Optional[Peasent]

    class Meta:
        identifier = "peasentpod"


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
    YIELD = "YIELD"
    CRITICAL ="CRITICAL"
    PENDING = "PENDING"


class ProvisionStatus(str, Enum):
    ERROR = "ERROR"
    PROGRESS = "PROGRESS"
    DONE = "DONE"
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
