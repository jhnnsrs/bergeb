from pydantic.main import BaseModel
from bergen.auths.legacy.app import LegacyApplication
from bergen.auths.backend.app import ArnheimBackendOauth
from bergen.auths.implicit.app import ImplicitApplication
from bergen.clients.base import ArkitektConfig, BaseBergen
from bergen.auths.types import GrantType, HerreConfig
import os
import yaml
import logging


logger = logging.getLogger(__name__)




class Bergen(BaseBergen):

    def __init__(self,
    config_path = "bergen.yaml",
    force_new_token = False,
    arkitekt_host: str = None, 
    arkitekt_port: int = None,
    herre_host: str = None,
    herre_port: int = None,
    client_id: str = None, 
    client_secret: str = None,
    username: str = None,
    password: str = None,
    grant_type: GrantType = None,
    bind=True,
    allow_insecure=False,
    **kwargs) -> None:


        arkitekt_config = {}
        herre_config = {}

        if os.path.isfile(config_path):
            with open(config_path,"r") as file:
                config = yaml.load(file, Loader=yaml.FullLoader)

                if "arkitekt" in config:
                    arkitekt_config.update(config["arkitekt"])

                if "herre" in config:
                    herre_config.update(config["herre"])

        else:
            raise Exception("No configuration file found! (please add to the directory or specify config_path")


        if arkitekt_host : arkitekt_config["port"]= arkitekt_host
        if arkitekt_port : arkitekt_config["host"]= arkitekt_port
        if herre_host : herre_config["host"]= herre_host
        if herre_port : herre_config["port"]= herre_port
        if client_id : herre_config["client_id"]= client_id
        if client_secret : herre_config["client_secret"]= client_secret
        if grant_type: herre_config["grant_type"] = grant_type

        
        if allow_insecure: 
            herre_config["secure"] = False
            arkitekt_config["secure"] = False
                
        herre_config = HerreConfig(**herre_config)
        arkitekt_config = ArkitektConfig(**arkitekt_config)


        if herre_config.authorization_grant_type == GrantType.BACKEND: auth = ArnheimBackendOauth(herre_config, force_new_token=force_new_token)
        elif herre_config.authorization_grant_type == GrantType.IMPLICIT: auth = ImplicitApplication(herre_config, force_new_token=force_new_token)
        elif herre_config.authorization_grant_type == GrantType.PASSWORD: auth = LegacyApplication(herre_config, username=username, password=password, force_new_token=force_new_token)
        else: raise NotImplementedError("Please Specifiy a valid Grant Type")

        super().__init__(auth, arkitekt_config, auto_negotiate=True, bind=bind, **kwargs)