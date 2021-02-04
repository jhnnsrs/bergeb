from bergen.clients.default import Bergen
from bergen.peasent.websocket import WebsocketPeasent

class HostBergen(WebsocketPeasent, Bergen):

    pass