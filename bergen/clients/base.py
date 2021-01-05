from bergen.logging import setLogging
from bergen.auths.base import BaseAuthBackend
from bergen.wards.base import BaseWard

import logging


logger = logging.getLogger(__name__)
import os


class BaseBergen:


    def __init__(self, auth: BaseAuthBackend, main_ward: BaseWard, auto_negotiate=True, bind=True, log=logging.INFO, local=None, **kwargs) -> None:
        
        if bind: 
            # We only import this here for typehints
            from bergen.registries.arnheim import set_current_arnheim
            set_current_arnheim(self)


        if log is not False:
            print(r"     _               _          _              ____ _ _            _    ")   
            print(r"    / \   _ __ _ __ | |__   ___(_)_ __ ___    / ___| (_) ___ _ __ | |_  ")
            print(r"   / _ \ | '__| '_ \| '_ \ / _ \ | '_ ` _ \  | |   | | |/ _ \ '_ \| __| ")
            print(r"  / ___ \| |  | | | | | | |  __/ | | | | | | | |___| | |  __/ | | | |_  ")
            print(r" /_/   \_\_|  |_| |_|_| |_|\___|_|_| |_| |_|  \____|_|_|\___|_| |_|\__| ")
            print(r"")
            setLogging(True, log)


        self.local = local if local is not None else os.getenv("ARNHEIM_LOCAL") == "1" 
        if self.local:
            logger.info("Running in Local Mode")
        self.auth = auth
        self.main_ward = main_ward
        self._transcript = None
        self.identifierDataPointMap = {}
        self.identifierWardMap: dict[str, BaseWard] = {}
        super().__init__()

        if auto_negotiate == True:
            self.negotiate()         

    @property
    def transcript(self):
        assert self._transcript is not None, "We have to negotiate first with our"
        return self._transcript


    def getExtensionSettings(self, extension):
        assert extension in self.transcript.extensions, f"Arnheim seems to have no idea about this Extension {extension}"
        return self.transcript.extensions[extension]


    def getWardForIdentifier(self, identifier):
        assert self._transcript is not None, "We cannot get query Identifiers on Datapoint before having negotiated them"
        if identifier in self.identifierWardMap:
            return self.identifierWardMap[identifier]
        else:
            return self.main_ward
            



    def negotiate(self, clientType = None):
        
        from bergen.constants import NEGOTIATION_GQL

        self._transcript = NEGOTIATION_GQL.run(ward=self.main_ward, variables={"clientType": clientType or self.auth.getClientType(), "local": self.local})
        logger.info(f"Successfully Got Protocols")
        
        assert self._transcript.models is not None, "We apparently didnt't get any points"

        from bergen.registries.datapoint import get_datapoint_registry
        datapoint_registry = get_datapoint_registry()

        self.identifierDataPointMap = {model.identifier.lower(): model.point for model in self._transcript.models}
        self.identifierWardMap = {model.identifier.lower(): datapoint_registry.getClientForData(model.point, self.auth) for model in self._transcript.models}

        logger.info("We established all Proper Clients for the interaction!")
        logger.info("Arnheim Ready!!!!!!!!")

    def getWard(self):
        return self.main_ward

    def _repr_html_(self):
        return f"""
            <p> Arnheim Client <p>
            <table>
                <tr>
                    <td> Connected to </td> <td> {self.main_ward.host} </td>
                </tr>
            </table>



        """
