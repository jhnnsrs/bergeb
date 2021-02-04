from bergen.types.model import ArnheimModel
from bergen.registries.matcher import get_current_matcher
from bergen.enums import TYPENAMES
from bergen.schema import Node
import logging

logger = logging.getLogger(__name__)

class ExpansionError(Exception):
    pass



async def expandInputs(node: Node, inputs: dict) -> dict:

    #assert node.inputs is not None, "Your Query for Nodes seems to not provide any field for inputs, please use that in your get statement"
    #assert len(node.inputs) > 0  is not None, "Your Node seems to not provide any inputs, calling is redundant"

    kwargs = {}
    for port in node.inputs:
        if port.key not in inputs:
            if port.required:
                raise ExpansionError(f"We couldn't expand {port.key} because it wasn't provided by our Inputs, wrong assignation!!!")
            else:
                break

        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            modelClass = get_current_matcher().getModelForIdentifier(identifier=port.identifier)
            instance =  await modelClass.asyncs.get(id=inputs[port.key])
            kwargs[port.key] = instance
        else:
            kwargs[port.key] = inputs[port.key]

    return kwargs



async def shrinkOutputs(node: Node, outputs: dict) -> dict:

    #assert node.inputs is not None, "Your Query for Nodes seems to not provide any field for inputs, please use that in your get statement"
    #assert len(node.inputs) > 0  is not None, "Your Node seems to not provide any inputs, calling is redundant"

    kwargs = {}
    for port in node.outputs:
        if port.key not in outputs:
            break

        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            instance = outputs[port.key]
            if isinstance(instance, ArnheimModel):
                kwargs[port.key] = outputs[port.key].id
            else:
                kwargs[port.key] = outputs[port.key]
        else:
            kwargs[port.key] = outputs[port.key]

    return kwargs



async def shrinkInputs(node: Node, inputs: dict) -> dict:

    #assert node.inputs is not None, "Your Query for Nodes seems to not provide any field for inputs, please use that in your get statement"
    #assert len(node.inputs) > 0  is not None, "Your Node seems to not provide any inputs, calling is redundant"

    kwargs = {}
    for port in node.inputs:
        if port.key not in inputs:
            break

        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            instance = inputs[port.key]
            if isinstance(instance, ArnheimModel):
                kwargs[port.key] = inputs[port.key].id
            else:
                kwargs[port.key] = inputs[port.key]
        else:
            kwargs[port.key] = inputs[port.key]

    return kwargs


async def expandOutputs(node: Node, outputs: dict, strict=False) -> dict:

    #assert node.inputs is not None, "Your Query for Nodes seems to not provide any field for inputs, please use that in your get statement"
    #assert len(node.inputs) > 0  is not None, "Your Node seems to not provide any inputs, calling is redundant"

    kwargs = {}
    for port in node.outputs:
        if port.key not in outputs:
            break

        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            try:
                modelClass = get_current_matcher().getModelForIdentifier(identifier=port.identifier)
                instance =  await modelClass.asyncs.get(id=outputs[port.key])
                kwargs[port.key] = instance
            except AssertionError as e:
                if strict: raise e
                logger.error(f"Couldn't expand outputs make sure to import the schema for {port.identifier}")
                kwargs[port.key] = outputs[port.key]
           
        else:
            kwargs[port.key] = outputs[port.key]

    return kwargs





