from bergen.messages.base import MessageDataModel, MessageMetaModel, MessageModel
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from bergen.messages.types import EXCEPTION


class ExceptionType(str, Enum):
    CLIENT = "client"
    ARNHEIM = "arnheim"
    PROVIDER = "provider"
    POD = "pod"

class ExceptionMetaMessage(MessageMetaModel):
    type: str = EXCEPTION


class ExceptionDataMessage(MessageDataModel):
    type: ExceptionType
    base: str
    message: str
    traceback: Optional[str] 

class ExceptionMessage(MessageModel):
    data: ExceptionDataMessage
    meta: ExceptionMetaMessage
