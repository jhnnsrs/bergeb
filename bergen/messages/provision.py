from bergen.messages.types import PROVISION
from bergen.messages.base import MessageDataModel, MessageMetaExtensionsModel, MessageMetaModel, MessageModel
from pydantic import BaseModel
from typing import Optional


class ProvisionParams(BaseModel):
    pass

class ProvisionMetaExtensionsModel(MessageMetaExtensionsModel):
    progress: Optional[str]
    callback: Optional[str]

class ProvisionMetaModel(MessageMetaModel):
    type: str = PROVISION
    extensions: Optional[ProvisionMetaExtensionsModel]

class ProvisionDataModel(MessageDataModel):
    
    #Meta
    parent: Optional[int]
    id: int
    reference: str

    #Inputs
    node: Optional[int] #TODO: Maybe not optional
    pod: Optional[int]
    template: Optional[int]
    params: Optional[ProvisionParams]
    
    #Status
    status: Optional[str]
    statusmessage: Optional[str]

class ProvisionMessage(MessageModel):
    data: ProvisionDataModel
    meta: ProvisionMetaModel