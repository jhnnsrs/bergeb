from bergen.enums import ClientType
from bergen.clients.default import Bergen
from bergen.models import Node
import asyncio
import time

client = Bergen(
        host="p-tnagerl-lab1",
        port=8000,
        client_id="y1W8JK5OgpAexf68eqbHIx60228rTBc4moNlaKYN", 
        client_secret="ovChuVgIFFQcNT3buPbm5AVjGCJGHBQZOQTqhvzwP02IllfJRVj17efit6aGqPcd01AJPY1SCc8kTBM22pistp8A1BRQRmtgX9Nycd2LcN1YEduhjpSY9mq5Pm2nV0xi",
        name="karl",
        client_type= ClientType.EXTERNAL
        # if we want to specifically only use pods on this innstance we would use that it in the selector
)

sleep = Node.objects.get(package="@canoncial/generic/filters", interface="sleep")

while input("Again?") in ["y","n"]:
    result = sleep.delay({"rep": 1})
    print(result)