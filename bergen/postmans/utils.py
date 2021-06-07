from bergen.messages import *

def build_assign_message(reference, reservation, args, kwargs, with_log=False, context=None, persist=False):
    assert reference is not None, "Must have a reference"

    data = {
                                    "reservation": reservation,
                                    "args": args, 
                                    "kwargs": kwargs,
    }

    meta = {
                                    "reference": reference, 
                                    "extensions": {
                                        "with_progress": with_log,
                                        "persist": persist
                                    }
    }

    if context:
        meta = {**meta, "context": context}
        return BouncedAssignMessage(data=data, meta=meta)

    else:
        return AssignMessage(data=data, meta=meta)



def build_unassign_messsage(reference, assignation, with_log=False, context=None, persist=False):
    assert reference is not None, "Must have a reference"
    data= {
                                        "assignation": assignation
    }
                                    
    meta={
                                    "reference": reference, 
                                    "extensions": {
                                        "with_progress": with_log,
                                        "persist": persist
                                    }
    }

    if context:
        meta = {**meta, "context": context}
        return BouncedUnassignMessage(data=data, meta=meta)

    else:
        return UnassignMessage(data=data, meta=meta)


def build_reserve_message(reference, node_id: str, template_id: str, provision: str, params_dict: dict = {}, with_log=False, context=None):
    assert reference is not None, "Must have a reference"
    assert node_id is not None or template_id is not None, "Please provide either a node_id or template_id"

    data={
                                "node": node_id, 
                                "template": template_id, 
                                "provision": provision,
                                "params": params_dict,
    }
    meta={
        "reference": reference,
        "extensions": {
            "with_progress": with_log,
        }
    }

    if context:
        meta = {**meta, "context": context}
        return BouncedReserveMessage(data=data, meta=meta)

    else:
        return ReserveMessage(data=data, meta=meta)



def build_unreserve_messsage(reference, reservation, with_log=False, context=None):
    assert reference is not None, "Must have a reference"
    data= {
                                        "reservation": reservation
    }
    
    meta={
                                    "reference": reference, 
                                    "extensions": {
                                        "with_progress": with_log
                                    }
    }

    if context:
        meta = {**meta, "context": context}
        return BouncedUnreserveMessage(data=data, meta=meta)

    else:
        return UnreserveMessage(data=data, meta=meta)

