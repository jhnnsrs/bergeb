from bergen.clients.base import BaseBergen

CURRENT_ARNHEIM = None

def get_current_arnheim() -> BaseBergen:
    global CURRENT_ARNHEIM
    if CURRENT_ARNHEIM is None:
        raise Exception("No Client was initialized before")
    else:
        return CURRENT_ARNHEIM


def set_current_arnheim(arnheim):
    global CURRENT_ARNHEIM
    CURRENT_ARNHEIM = arnheim