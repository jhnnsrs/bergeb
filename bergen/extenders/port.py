from bergen.extenders.base import BaseExtender
import logging

logger = logging.getLogger(__name__)

class PortExtender(BaseExtender):


    def provide(template = None, provider = None, **kwargs):
        logger.info("Starting provision")



    def __call__(inputs: dict, provider="vard"):
        logger.info("Called with inputs")

        logger.info("Serializing Inputs")


    def _repr_html_(self):
        string = f"{self.TYPENAME} with {self.key}"

        return string

