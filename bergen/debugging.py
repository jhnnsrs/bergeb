from bergen.messages.types import DEACTIVATE_POD
from enum import Enum

class DebugLevel(str, Enum):
    INFO = "INFO"
    DEBUG = "DEBUG"

stylemap = {
    DebugLevel.INFO: "[magenta]",
    DebugLevel.DEBUG: "[green]"
}

def get_style_for_level(level: DebugLevel):
    return stylemap[level]



