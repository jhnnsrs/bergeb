from abc import ABC
import logging

logger = logging.getLogger(__name__)

def hookable(hook, overwritable=False):

    def real_decorator(function):
        async def wrapped(self, *args, **kwargs):
            if hook in self.hooks.overwritten_hooks:
                try:
                    assert overwritable, "The function was requested to be overwritten but cannot be overwritten (hookable overwrite false)"
                    return await self.hooks.overwritten_hooks[hook](self, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Overwritten Hook Exception. Resorting to original Function! {e}")
            if hook in self.hooks.passing_hooks:
                try:
                    await self.hooks.passing_hooks[hook](self, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Passing Hook Exception: {e}")

            return await function(self, *args, **kwargs)
        return wrapped

    return real_decorator



class Hooks:

    def __init__(self) -> None:
        self.overwritten_hooks = {}
        self.passing_hooks = {}
        pass

    def addHook(self, hook, function, overwrite=False):
        if overwrite:
            self.overwritten_hooks[hook] = function
        else:
            self.passing_hooks[hook] = function

class Hookable(ABC):

    def __init__(self, hooks: Hooks=None) -> None:
        super().__init__()
        self.hooks = hooks