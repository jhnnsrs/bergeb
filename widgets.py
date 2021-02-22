#%%
from PyQt5 import QtWidgets
from bergen.clients.default import Bergen
from bergen.models import Node
import asyncio
import time
from bergen.query import QueryList
from PyQt5.QtWidgets import QApplication, QWidget
import sys


Bergen(
                host="localhost",
                port=8000,
                client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
                client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
                name="frankomanko",
                jupyter=True,
                force_sync=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)

#%% 




if __name__ == "__main__":


    app = QApplication([])

    node = Node.objects.get(package="basic", interface="sleep")
    inputs = node.askInputs()

    x = node(inputs, with_progress=True)
    print(x)
