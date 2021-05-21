from bergen.models import Node






def use(package=None, interface=None) -> Node:
    """Use a Node on the Platform by Searching for it on its package

    Args:
        package ([type], optional): The package this Node belongs to. Defaults to None.
        interface ([type], optional):  The interface of this Node. Defaults to None.

    Returns:
        Node: The Node
        
    """
    return Node.objects.get(package=package, interface=interface)

