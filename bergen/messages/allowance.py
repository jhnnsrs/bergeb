from bergen.messages.types import ALLOWANCE
from bergen.messages.base import MessageDataModel, MessageMetaExtensionsModel, MessageMetaModel, MessageModel
from pydantic import BaseModel
from typing import List, Mapping, Optional


class AllowanceMetaModel(MessageMetaModel):
    type: str = ALLOWANCE

class AllowanceDataModel(MessageDataModel):
    pod_template_map: Mapping[int, int]


class AllowanceMessage(MessageModel):
    data: AllowanceDataModel
    meta: AllowanceMetaModel = {"type": ALLOWANCE}