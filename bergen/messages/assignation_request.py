from bergen.messages.types import ASSIGNATION_REQUEST
from bergen.messages.base import MessageDataModel, MessageMetaExtensionsModel, MessageMetaModel, MessageModel
from pydantic import BaseModel
from typing import Optional


class AssignationRequestParams(BaseModel):
    pass

class AssignationRequestMetaAuthModel(MessageMetaExtensionsModel):
    token: str

class AssignationRequestMetaExtensionsModel(MessageMetaExtensionsModel):
    progress: Optional[str]

class AssignationRequestMetaModel(MessageMetaModel):
    type: str = ASSIGNATION_REQUEST
    auth: AssignationRequestMetaAuthModel
    extensions: Optional[AssignationRequestMetaExtensionsModel]

class AssignationRequestDataModel(MessageDataModel):
    node: Optional[int] #TODO: Maybe not optional
    pod: Optional[int]
    template: Optional[int]
    reference: str
    callback: Optional[str]
    progress: Optional[str]

    inputs: dict
    params: Optional[AssignationRequestParams]


class AssignationRequestMessage(MessageModel):
    data: AssignationRequestDataModel
    meta: AssignationRequestMetaModel