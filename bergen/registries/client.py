from bergen.clients.base import BaseBergen

CURRENT_CLIENT = None

def get_current_client() -> BaseBergen:
    global CURRENT_CLIENT
    if CURRENT_CLIENT is None:
        raise Exception("No Client was initialized before")
    else:
        return CURRENT_CLIENT


def set_current_client(arnheim):
    global CURRENT_CLIENT
    CURRENT_CLIENT = arnheim