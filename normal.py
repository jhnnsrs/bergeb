import asyncio
import time

from aiostream import async_, pipe, stream

from bergen.clients.default import Bergen
from bergen.enums import ClientType
from bergen.models import Node
from bergen.query import TypedGQL


def main():

    client = Bergen(
        host="p-tnagerl-lab1",
        port=8000,
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        name="giaocomo",
    )

    segmentor = Node.objects.get(package="basic", interface="segmentor")
    print(segmentor)

    segmentor.provide({})





if __name__ == "__main__":
    main()
