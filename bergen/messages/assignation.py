from bergen.messages.types import ASSIGNATION
from bergen.messages.base import MessageDataModel, MessageMetaExtensionsModel, MessageMetaModel, MessageModel
from pydantic import BaseModel
from typing import Optional


class AssignationParams(BaseModel):
    pass

class AssignationMetaExtensionsModel(MessageMetaExtensionsModel):
    progress: Optional[str]

class AssignationMetaModel(MessageMetaModel):
    type: str = ASSIGNATION
    extensions: Optional[AssignationMetaExtensionsModel]

class AssignationDataModel(MessageDataModel):
    id: int
    node: Optional[int] #TODO: Maybe not optional
    pod: Optional[int]
    template: Optional[int]
    status: Optional[str]
    statusmessage: Optional[str]
    reference: str
    callback: Optional[str]
    progress: Optional[str]

    inputs: dict
    outputs: Optional[dict]
    params: Optional[AssignationParams]


class AssignationMessage(MessageModel):
    data: AssignationDataModel
    meta: AssignationMetaModel