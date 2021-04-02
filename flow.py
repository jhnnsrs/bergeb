from abc import abstractmethod
from bergen.messages.postman.provide.bounced_provide import BouncedProvideMessage
from bergen.extenders.node import Reservation
from bergen.entertainer.actor import AsyncFuncActor, AsyncGenActor, HostHelper
from bergen.messages.postman import AssignMessage
from bergen.schema import NodeType, Pod, Template
from bergen.provider.base import OneExlusivePodPolicy
from typing import Dict, List, Tuple
from bergen.clients.provider import ProviderBergen
from fluss.schema import Graph
from fluss import diagram
import asyncio
import logging
from bergen.models import Node

logger = logging.getLogger(__name__)


class Constants(dict):
    pass

class Layout:


    def __init__(self, di: diagram.Diagram) -> None:
        self.nodes: List[diagram.Node] = [ node for node in di.elements if isinstance(node, diagram.Node)]
        self.edges: List[diagram.Edge] = [ edge for edge in di.elements if isinstance(edge, diagram.Edge)]

        self.nodeIDNodeMap = {node.id: node for node in self.nodes}
        self.edgeIDEdgeMap = {edge.id: edge for edge in self.edges}

        self.argNode = next((node for node in  self.nodes if isinstance(node, diagram.ArgNode)), None) # We only want the first one
        self.kwargNode = next((node for node in  self.nodes if isinstance(node, diagram.KwargNode)), None) # We only want the first one
        self.returnNode = next((node for node in  self.nodes if isinstance(node, diagram.ReturnNode)), None) # We only want the first one

        self.non_generic_nodes = [node for node in self.nodes if not isinstance(node, (diagram.ArgNode, diagram.KwargNode, diagram.ReturnNode))]
        print(self.non_generic_nodes)
        print(self.edges)

    def connectedEdges(self, node_id: str, sourceHandle: str = None):
        return [edge for edge in self.edges if edge.source == node_id and (sourceHandle is None or edge.sourceHandle == sourceHandle)]

    def connectedNodes(self, node_id: str, sourceHandle: str = None, targetHandle: str = None):
        edg_ids = [edge.target for edge in self.connectedEdges(node_id, sourceHandle) if targetHandle is None or edge.targetHandle == targetHandle]
        nodes =  [node for node in self.nodes if node.id in edg_ids]
        return nodes


    def connectedNodesWithHandle(self, node_id: str, sourceHandle: str = None):
        edges = [edge for edge in self.connectedEdges(node_id, sourceHandle)]
        return [(edge.targetHandle, self.nodeIDNodeMap[edge.target]) for edge in edges]

    def getInitialNodes(self):
        non_kwargs_edge_targets = [edge.target for edge in self.edges if edge.source != self.kwargNode.id]
        print(non_kwargs_edge_targets)
        non_generic_nodes_that_are_not_targets = [node for node in self.non_generic_nodes if node.id not in non_kwargs_edge_targets]
        print(non_generic_nodes_that_are_not_targets)
        return non_generic_nodes_that_are_not_targets




class NodeRun:

    def __init__(self, actionQueue: asyncio.Queue, node: diagram.Node) -> None:
        self.action_queue = actionQueue
        self.node = node
        pass
    
    @abstractmethod
    async def assignHandle(self, handle, args):
        raise NotImplementedError("Needs to be implemented")

    async def pushHandle(self, handle, return_or_yield):
        await self.action_queue.put((self.node.id, handle, return_or_yield))

    @abstractmethod
    async def run(self):
        raise NotImplementedError("Needs to be implemented")


class ZipNode(NodeRun):


    def __init__(self, actionQueue: asyncio.Queue,  node: diagram.Node) -> None:
        super().__init__(actionQueue, node)
        self.arg_one_queue = asyncio.Queue()
        self.arg_two_queue = asyncio.Queue()

    async def assignHandle(self, handle, args):
        if handle == "arg1": await self.arg_one_queue.put(args)
        elif handle == "arg2": await self.arg_two_queue.put(args)
        else: raise Exception(f"Unknown Handle {handle}")

    async def run(self):
        while True:
            returns = await asyncio.gather(self.arg_one_queue.get(), self.arg_two_queue.get())
            await self.pushHandle("return", returns)


class AsnycNode(NodeRun):

    def __init__(self, actionQueue: asyncio.Queue,  node: diagram.Node , res: Reservation, constants: Constants) -> None:
        super().__init__(actionQueue, node)
        self.arg_queue = asyncio.Queue()
        self.contants = constants
        self.res = res

    @abstractmethod
    async def assignHandle(self, handle, args):
        assert handle == "args", f"Unknown Handle {handle}"
        await self.arg_queue.put(args)

    async def push(self, return_or_yield):
        await self.pushHandle("returns", return_or_yield)

async def fake_func(*args, **kwargs):
    await asyncio.sleep(1)
    return args

async def fake_gen(*args, **kwargs):
    for i in range(0,10):
        await asyncio.sleep(1)
        yield args


class FuncNode(AsnycNode):

    async def run(self):
        while True:
            args = await self.arg_queue.get()
            logger.info(f"Calling Node {self.node.data.node.name} as Func")
            #returns = await self.res.assign(*args, **self.contants)
            returns = await fake_func(*args, **self.contants)
            logger.info(f"Pushing {returns}")
            await self.push(returns)


class GenNode(AsnycNode):

    async def run(self):
        while True:
            args = await self.arg_queue.get()
            logger.info(f"Calling Node {self.node.data.node.name} as Gen")
            #async for returns in self.res.stream(*args, **self.contants):
            #    await self.push(returns)
            async for returns in fake_gen(*args, **self.contants):
                logger.info(f"Pushing {returns}")
                await self.push(returns)



class Flow(AsyncGenActor):
    """ Flow Base receives a Pod with an attached template """

    def __init__(self, pod: Pod, helper: HostHelper) -> None:
        super().__init__(pod, helper)

        self.arg_queue = asyncio.Queue()
        self.return_queue = asyncio.Queue()


    async def on_provide(self):
        # graph = await Graph.asyncs.get(template=self.pod.template)
        self.graph = await Graph.asyncs.get(id=59)

        self.diagram = self.graph.diagram
        self.nodes: List[diagram.Node] = [ node for node in self.diagram.elements if isinstance(node, diagram.Node)]
        self.edges: List[diagram.Edge] = [ edge for edge in self.diagram.elements if isinstance(edge, diagram.Edge)]
    
        self.argNode = next((node for node in  self.nodes if isinstance(node, diagram.ArgNode)), None) # We only want the first one
        self.kwargNode = next((node for node in  self.nodes if isinstance(node, diagram.KwargNode)), None) # We only want the first one
        self.returnNode = next((node for node in  self.nodes if isinstance(node, diagram.ReturnNode)), None) # We only want the first one

        self.arkitektNodes = [node for node in  self.nodes if isinstance(node, diagram.ArkitektNode)]

        
        logger.info(f"Querying Arkitekt Nodes")
        nodeIDs = [node.id for node in self.arkitektNodes]
        nodeSelectors = [node.data.selector for node in self.arkitektNodes]
        nodeInstanceFutures = [Node.asyncs.get(id=node.data.node.id)for node in self.arkitektNodes]
        nodeInstances = await asyncio.gather(*nodeInstanceFutures)

        logger.info(f"Reserving Arkitekt Nodes")
        reservationsContexts = [node.reserve(**selector.dict()) for node, selector in zip(nodeInstances, nodeSelectors)]
        reservationEnterFutures = [res.__aenter__() for res in reservationsContexts]
        self.reservations = await asyncio.gather(*reservationEnterFutures)


        logger.info(f"Building a Reservation Map")
        self.nodeIDReservationMap = { node_id: reservation for node_id, reservation in zip(nodeIDs, self.reservations)}
        print(self.nodeIDReservationMap)


        if self.argNode: print(self.argNode)
        if self.kwargNode: print(self.kwargNode)
        if self.returnNode: print(self.returnNode)

        
        logger.info(f"Reserved everything")

    async def assign(self, *args, **kwargs) -> int:
        """Adder

            Adds x + y

            Args:
                helper ([type]): [description]
                x (int): Input X
                y (int): Input Y

            Returns:
                int: X + Y
        """
        assert len(self.argNode.data.args) == len(args), "Received different arguments then our ArgNode requires"
        assert len(self.kwargNode.data.kwargs) == len(kwargs.items()), "Received different arguments then our ArgNode requires"


        layout = Layout(self.diagram)

        action_queue = asyncio.Queue()

        self.nodeIDConstantsMap: Dict[str, Constants] = {}

        for kwarg, value  in kwargs.items():
            for kwarg_handle, node in layout.connectedNodesWithHandle(self.kwargNode.id, f"kwarg_{kwarg}"):
                kwarg = kwarg_handle[len("kwarg_"):]
                self.nodeIDConstantsMap.setdefault(node.id, {})[kwarg] = value


        logger.info(f"Created Constants for this Run {self.nodeIDConstantsMap}")

        runs: List[Tuple[str, NodeRun]] = []

        logger.info("Instantiating Node Runs: Creating All necessary Queues for our Eventbus")
        for node in self.nodes:
            print("nananana", node)
            if isinstance(node, diagram.ArkitektNode):
                res = self.nodeIDReservationMap[node.id]
                constants = self.nodeIDConstantsMap.get(node.id, {})
                if node.data.node.type == NodeType.GENERATOR:
                    runs.append((node.id, GenNode(action_queue, node, res, constants)))


        tasks = []
        logger.info("Creating Runs as tasks")
        for id, run in runs:
            tasks.append((id, asyncio.create_task(run.run())))


        nodeIDRunMap = {id: run for id, run in runs}
        nodeIDTaskMap = {id: task for id, task in tasks}

        print(nodeIDRunMap)
        # We send our first arguments 

        initial_nodes = layout.getInitialNodes()
        logger.info(f"This nodes have no args and will automatically be called: {initial_nodes}")


        logger.info(f"Starting Initial Nodes (Nodes that need no Args)  {initial_nodes}")
        await asyncio.gather(*[nodeIDRunMap[node.id].assignHandle("args", []) for node in initial_nodes])



        arg_receiving_nodes = layout.connectedNodes(self.argNode.id)
        logger.info(f"This nodes will receive args: {arg_receiving_nodes}")

        initial_actions = []
        for node in arg_receiving_nodes:
            initial_actions.append((node.id, "returns", args))

        
        logger.info(f"Assigning args to Action Bus {initial_actions}")
        await asyncio.gather(*[action_queue.put(action) for action in initial_actions])

        while True:
            node_id, output_handle, values = await action_queue.get()
            logger.info(f"Searching for nodes {node.id} on {output_handle}: {values}")
            # Action follows NODE_ID, OUTPUT_HANDLE, VALUES
            handle_nodes = layout.connectedNodesWithHandle(node_id, output_handle)
            logger.info(f"Found the Following handles {handle_nodes}")

            for handle, node in handle_nodes:
                if isinstance(node, diagram.ReturnNode):
                    yield values
                else:
                    logger.info(f"Assigning to {node.id} on {handle}: {values}")
                    await nodeIDRunMap[node.id].assignHandle(handle, values)

            action_queue.task_done()


    async def on_unprovide(self):
        logger.warning("Gently deleting our reservations")
        self.reservations = await asyncio.gather(*[res.__aexit__() for res in self.reservations])
        logger.warning("UNreserved")






async def main():

    async with ProviderBergen(
        config_path="fluss.yaml",
        name="Fluss",
        force_new_token=True,
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
    ) as client:

        @client.hook("bounced_provide", overwrite=True)
        async def on_bounced_provide(self, bounced_provide: BouncedProvideMessage):
            logger.error("Nana")


        await client.provide_async()


        acting = Flow(None, None)
        await acting.on_provide()

        async for i in acting.assign(timer=5):
            logger.info(f"Yielding {i}")

        await acting.on_unprovide()




asyncio.run(main())
