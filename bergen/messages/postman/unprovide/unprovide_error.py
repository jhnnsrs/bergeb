from pydantic.main import BaseModel
from ....messages.types import  PROVIDE, PROVIDE_DONE, UNPROVIDE_ERROR
from ....messages.base import MessageDataModel, MessageMetaExtensionsModel, MessageMetaModel, MessageModel
from typing import List, Optional


class MetaExtensionsModel(MessageMetaExtensionsModel):
    # Set by postman consumer
    progress: Optional[str]
    callback: Optional[str]

class MetaModel(MessageMetaModel):
    type: str = UNPROVIDE_ERROR
    extensions: Optional[MetaExtensionsModel]

class DataModel(MessageDataModel):
    provision: str #TODO: Maybe not optional

class UnprovideErrorMessage(MessageModel):
    data: DataModel
    meta: MetaModel