from bergen.schema import PodStatus
import logging


logger = logging.getLogger(__name__)
class HostedPod():

    def __init__(self, node, params, enter_when: PodStatus = PodStatus.ACTIVE, **kwargs) -> None:
        self.node = node
        self.assigned_pod = None
        self.provision_kwargs = kwargs
        self.provision_params = params
        self.enter_when = enter_when
        pass



    async def __aenter__(self) -> "Pod":
        self.assigned_pod = await self.node.provide_async(self.provision_params, **self.provision_kwargs, return_when=self.enter_when)
        return self.assigned_pod

    async def __aexit__(self, exc_type, exc, tb):
        logger.info('Exiting Rabbit')
        await self.assigned_pod.unprovide()