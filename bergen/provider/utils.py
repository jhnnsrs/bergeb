
from bergen.models import Node, NodeType
from typing import Callable, Type
from bergen.types.node.ports.arg import IntArgPort, ModelArgPort, StringArgPort
from bergen.types.node.ports.kwarg import IntKwargPort, ModelKwargPort, StringKwargPort
from bergen.types.node.ports.returns import IntReturnPort, ModelReturnPort
from bergen.types.model import ArnheimModel
import inspect
import logging
from inspect import signature, Parameter
from docstring_parser import parse

logger = logging.getLogger(__name__)


def createNodeFromActor(actor,*args, **kwargs):
    raise NotImplementedError("No longer supported")
    #return createNodeFromFunction(actor.assign, *args, interface=actor.__name__.lower())

def createNodeFromFunction(function: Callable, widgets: dict = {}, allow_empty_doc=False, interface=None):
    is_generator = inspect.isasyncgenfunction(function) or inspect.isgenerator(function)
    logger.info(f"Node is {'Generator' if is_generator else 'Function'}")

    sig = signature(function)
    # Generate Args and Kwargs from the Annotation
    args = []
    kwargs = []
    function_inputs = sig.parameters
    for key, value in function_inputs.items():
        widget = widgets.get(key, None)
        the_class = value.annotation

        if value.default == Parameter.empty: # Non default parameters are args
            if issubclass(the_class, ArnheimModel):
                args.append(ModelArgPort.fromParameter(value, the_class, widget=widget))
            if issubclass(the_class, int):
                args.append(IntArgPort.fromParameter(value, widget=widget))
            if issubclass(the_class, str):
                args.append(StringArgPort.fromParameter(value, widget=widget))
        else:
            if issubclass(the_class, ArnheimModel):
                kwargs.append(ModelKwargPort.fromParameter(value, the_class, widget=widget))
            if issubclass(the_class, int):
                kwargs.append(IntKwargPort.fromParameter(value, widget=widget))
            if issubclass(the_class, str):
                args.append(StringKwargPort.fromParameter(value, widget=widget))



    # Generate types from the Output
    returns = []

    function_output = sig.return_annotation
    try:
        # Raises type error if we use it with a class but needed here because typing is actually not a class but an Generic Alias :rolling_eyes::
        if function_output._name == "Tuple":
            for type in function_output.__args__:
                if issubclass(type, ArnheimModel):
                    returns.append(ModelReturnPort(value, key=type.__name__))
                if issubclass(type, int):
                    returns.append(IntReturnPort(key=type.__name__))

    except AttributeError:
        # Once here we should have only classes... lets see about that
        if issubclass(function_output, ArnheimModel):
                returns.append(ModelReturnPort(function_output, key=function_output.__name__))
        if issubclass(function_output, int):
                returns.append(IntReturnPort(key=function_output.__name__))

    # Docstring Parser to help with descriptions
    docstring = parse(function.__doc__)
    if docstring.long_description is None:
        assert allow_empty_doc is not False, f"We don't allow empty documentation for function {function.__name__}. Please Provide"
        logger.warn(f"Allowing empty Documentatoin. Please consider providing a documentation for function {function.__name__}")


    name = interface or docstring.short_description or function.__name__
    description = docstring.long_description or "No Description"

    doc_param_map = {param.arg_name: {
        "required": not param.is_optional,
        "description": param.description if not param.description.startswith("[") else None,
    } for param in docstring.params}


    if docstring.returns:
        return_description = docstring.returns.description
        seperated_list = return_description.split(",")
        assert len(returns) == len(seperated_list), "Length of Description and Returns not Equal: If you provide a Return Annotation make sure you seperate the description for each port with ','"
        for index, doc in enumerate(seperated_list):
            returns[index].description = doc

    # TODO: Update with documentatoin.... (Set description for portexample)
    for port in args:
        if port.key in doc_param_map:
            updates = doc_param_map[port.key]
            port.description = updates["description"] or port.description

    for port in kwargs:
        if port.key in doc_param_map:
            updates = doc_param_map[port.key]
            port.description = updates["description"] or port.description


    logger.info(f"Creating Arg Ports: {[str(port.key) for  port in args]}")
    logger.info(f"Creating Kwargs Ports: {[str(port.key) for  port in kwargs]}")
    logger.info(f"Creating Returns Ports: {[str(port.key) for  port in returns]}")

    return Node.objects.update_or_create(
        name = name,
        interface = interface or function.__name__,
        description = description,
        args = [arg.serialize() for arg in args],
        kwargs = [kwarg.serialize() for kwarg in kwargs],
        returns = [re.serialize() for re in returns],
        type = NodeType.GENERATOR if is_generator else NodeType.FUNCTION
    )