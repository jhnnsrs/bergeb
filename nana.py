from typing import TypedDict
from bergen.clients.host import HostBergen


client = HostBergen(
        host="p-tnagerl-lab1",
        port=8090,
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        name="imagej",
        force_sync=True,
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
)



@client.enable(gpu=True)
def sobelFilter(helper, sigma: int, file_path: int) -> TypedDict("", sigma=int):
    """Sobel Filter

    Sobel filter filters an image with a sobel filter
    """
    print("logici")

    return { "sigma": 5}




client.run()