from bergen.actors.utils import useUser
from bergen.clients.provider import ProviderBergen
from bergen import use, log
import asyncio
import logging
import random
import time
from grunnlag.schema import Sample
logger = logging.getLogger(__name__)

client = ProviderBergen(
        config_path = "implicit.yaml",
        log_stream = True,
        force_new_token=True,
        auto_reconnect=True #if we want to specifically only use pods on this innstance we would use that it in the selector
)

client.negotiate()


@client.provider.enable(gpu=True)
def adder(x: int, y: int, z: int = 7) -> int:
        """Adder

        Adds x + y

        Args:
            x (int): Input X
            y (int): Input Y

        Returns:
            int: X + Y
        """
        log("hsnsns")

        for i in range(2):
            log(f"Sleeping {i}")
            time.sleep(1)
            yield x + y



client.provide()