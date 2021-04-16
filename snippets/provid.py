
class ProvideContext:


    def __init__(self, node, on_progress=None, **params) -> None:
        bergen = get_current_arnheim()

        self._postman = bergen.getPostman()
        self.node = node
        self.on_progress = on_progress
        self.params = ProvisionParams(**params)
        pass


    async def assign(self, *args, **kwargs):
        return await self._postman.assign(pod=self.pod, node=self.node, args=args, kwargs=kwargs, on_progress=self.on_progress)


    async def unprovide(self):
        return await self._postman.unprovide(pod=self.pod, on_progress=self.on_progress)

    async def provide(self):
        return await self._postman.provide(node=self.node, params=self.params, on_progress=self.on_progress)

    async def __aenter__(self):
        logger.info(f"Providing this node {self.node} with {self.params}")
        self.pod = await self.provide()
        logger.warn(f"Provided Listener on {self.pod.channel}")
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.unprovide()
