import re
from typing import List, Tuple
from bergen.types.model import ArnheimModel
from bergen.registries.matcher import get_current_matcher
from bergen.enums import TYPENAMES
from bergen.schema import Node
import logging

logger = logging.getLogger(__name__)

class ExpansionError(Exception):
    pass



async def expandInputs(node: Node, args: dict, kwargs: dict) -> dict:

    #assert node.inputs is not None, "Your Query for Nodes seems to not provide any field for inputs, please use that in your get statement"
    #assert len(node.inputs) > 0  is not None, "Your Node seems to not provide any inputs, calling is redundant"

    expanded_args = {}
    for port in node.args:
        if port.key not in args:
            if port.required:
                raise ExpansionError(f"We couldn't expand {port.key} because it wasn't provided by our Args, wrong assignation!!!")
            else:
                break

        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            modelClass = get_current_matcher().getModelForIdentifier(identifier=port.identifier)
            instance =  await modelClass.asyncs.get(id=args[port.key])
            expanded_args[port.key] = instance
        else:
            expanded_args[port.key] = args[port.key]

    expanded_kwargs = {}
    for port in node.kwargs:
        if port.key not in kwargs:
            if port.required:
                raise ExpansionError(f"We couldn't expand {port.key} because it wasn't provided by our Kwargs, wrong assignation!!!")
            else:
                break

        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            modelClass = get_current_matcher().getModelForIdentifier(identifier=port.identifier)
            instance =  await modelClass.asyncs.get(id=args[port.key])
            expanded_kwargs[port.key] = instance
        else:
            expanded_kwargs[port.key] = kwargs[port.key]





    return expanded_args, expanded_kwargs



async def shrinkOutputs(node: Node, returns: List) -> dict:

    #assert node.inputs is not None, "Your Query for Nodes seems to not provide any field for inputs, please use that in your get statement"
    #assert len(node.inputs) > 0  is not None, "Your Node seems to not provide any inputs, calling is redundant"

    shrank_returns = []
    if not isinstance(returns, tuple) or isinstance(returns, list):
        returns = [returns]

    assert len(node.returns) == len(returns), "Returns do not conform to Node definition"
    for port, item in zip(node.returns, returns):
        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            if isinstance(item, ArnheimModel):
                shrank_returns.append(item.id)
            else:
                shrank_returns.append(item)
        else:
            shrank_returns.append(item)

    return shrank_returns



async def shrinkInputs(node: Node, args: List, kwargs: List) -> Tuple[dict, dict]:

    #assert node.inputs is not None, "Your Query for Nodes seems to not provide any field for inputs, please use that in your get statement"
    #assert len(node.inputs) > 0  is not None, "Your Node seems to not provide any inputs, calling is redundant"

    shrinked_args = {}
    for arg, port in zip(args, node.args):
        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            instance = arg
            if isinstance(instance, ArnheimModel):
                shrinked_args[port.key] = arg.id
            else:
                shrinked_args[port.key] = arg
        else:
            shrinked_args[port.key] = arg


    shrinked_kwargs = {}
    for port in node.kwargs:
        if port.key not in kwargs:
            break

        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            instance = kwargs[port.key]
            if isinstance(instance, ArnheimModel):
                shrinked_kwargs[port.key] = kwargs[port.key].id
            else:
                shrinked_kwargs[port.key] = kwargs[port.key]
        else:
            shrinked_kwargs[port.key] = kwargs[port.key]
    
    return shrinked_args, shrinked_kwargs


async def expandOutputs(node: Node, returns: dict, strict=False) -> List:

    #assert node.inputs is not None, "Your Query for Nodes seems to not provide any field for inputs, please use that in your get statement"
    #assert len(node.inputs) > 0  is not None, "Your Node seems to not provide any inputs, calling is redundant"

    expanded_returns = []
    assert len(node.returns) == len(returns), "Returns do not conform to Node definition. Someone might have intercepted a Request"
    for port, item in zip(node.returns, returns):
        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            try:
                modelClass = get_current_matcher().getModelForIdentifier(identifier=port.identifier)
                instance =  await modelClass.asyncs.get(id=item)
                expanded_returns.append(instance)
            except AssertionError as e:
                if strict: raise e
                logger.error(f"Couldn't expand outputs make sure to import the schema for {port.identifier}")
                expanded_returns.append(item)
        else:
            expanded_returns.append(item)

    return expanded_returns





