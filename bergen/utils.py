from bergen.registries.matcher import get_current_matcher
from bergen.enums import TYPENAMES
from bergen.schema import Node


class ExpansionError(Exception):
    pass



def expandInputs(node: Node, inputs: dict) -> dict:

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
            instance =  modelClass.objects.get(id=inputs[port.key])
            kwargs[port.key] = instance
        else:
            kwargs[port.key] = inputs[port.key]

    return kwargs


def expandOutputs(node: Node, inputs: dict) -> dict:

    kwargs = {}
    for port in node.outputs:
        if port.TYPENAME == TYPENAMES.MODELPORTTYPE:
            modelClass = get_current_matcher().getModelForIdentifier(identifier=port.identifier)
            instance =  modelClass.objects.get(id=inputs[port.key])
            kwargs[port.key] = instance
        else:
            kwargs[port.key] = inputs[port.key]

    return kwargs




