from bergen.debugging import DebugLevel
from bergen.handlers import AssignHandler, ReserveHandler, ProvideHandler
import contextvars


assign_handler_context  = contextvars.ContextVar('assign_handler', default=None)
reserve_handler_context = contextvars.ContextVar("reserve_handler", default=None)
provide_handler_context = contextvars.ContextVar("provide_handler", default=None)


async def log(message, level: DebugLevel = DebugLevel.INFO):
    handler: AssignHandler = assign_handler_context.get()
    await handler.log(message, level)
