from bergen.models import Node
import asyncio




def use(package=None, interface=None) -> Node:
    """Use a Node on the Platform by Searching for it on its package

    Args:
        package ([type], optional): The package this Node belongs to. Defaults to None.
        interface ([type], optional):  The interface of this Node. Defaults to None.

    Returns:
        Node: The Node
        
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return Node.asyncs.get(package=package, interface=interface)
    else:
        return Node.objects.get(package=package, interface=interface)

