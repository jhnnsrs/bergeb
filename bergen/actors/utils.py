import asyncio
from bergen.debugging import DebugLevel
from bergen.handlers import AssignHandler, ReserveHandler, ProvideHandler
import contextvars

loop_context = contextvars.ContextVar("loop_context", default=None)
assign_handler_context  = contextvars.ContextVar('assign_handler', default=None)
provide_handler_context = contextvars.ContextVar("provide_handler", default=None)


async def log_async(message, level: DebugLevel = DebugLevel.INFO):
    handler: AssignHandler = assign_handler_context.get()
    await handler.log(message, level)


def log(message: str, level: DebugLevel = DebugLevel.INFO):
    """ Logs a message

    Depending on both the configuration of Arkitekt and the overwrite set on the
    Assignment, this logging will be sent (and persisted) on the Arkitekt server

    Args:
        message (sr): The Message you want to send
        level (DebugLevel, optional): The level of the log. Defaults to DebugLevel.INFO.

    Returns:
        [Future]: Returns a future if currently running in an event loop
    """
    try:
        event_loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = loop_context.get()
        loop.create_task(log_async(message, level))
    else:
        if event_loop.is_running():
            return log_async(message, level=level)