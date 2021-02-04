from bergen.messages.types import PROVISION_REQUEST
from bergen.messages.base import MessageDataModel, MessageMetaExtensionsModel, MessageMetaModel, MessageModel
from pydantic import BaseModel
from typing import Optional


class ProvisionRequestParams(BaseModel):
    pass

class ProvisionRequestMetaAuthModel(MessageMetaExtensionsModel):
    token: str

class ProvisionRequestMetaExtensionsModel(MessageMetaExtensionsModel):
    progress: Optional[str]
class ProvisionRequestMetaModel(MessageMetaModel):
    type: str = PROVISION_REQUEST
    auth: ProvisionRequestMetaAuthModel
    extensions: Optional[ProvisionRequestMetaExtensionsModel]

class ProvisionRequestDataModel(MessageDataModel):
    node: Optional[int] 
    template: Optional[int]
    callback: Optional[str]
    progress: Optional[str]
    reference: str
    params: Optional[ProvisionRequestParams]


class ProvisionRequestMessage(MessageModel):
    data: ProvisionRequestDataModel
    meta: ProvisionRequestMetaModel