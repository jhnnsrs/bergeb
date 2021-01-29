from bergen.schema import Node
from bergen.types.node.inputs import Inputs, Outputs
from bergen.managers.model import ModelManager
from bergen.queries.delayed.node import NODE_QUERY, CREATE_NODE_MUTATION
from typing import Type


class NodeManager(ModelManager[Node]):

    def get_or_create(self, inputs: Type[Inputs] = None, outputs: Type[Outputs] = None , **kwargs) -> Node:
        
        parsed_inputs = inputs.serialized
        parsed_outputs = outputs.serialized
        
        node = CREATE_NODE_MUTATION(self.model).run(variables={
            "inputs" : parsed_inputs,
            "outputs": parsed_outputs,
            **kwargs

        })
        return node