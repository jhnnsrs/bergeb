
from bergen.types.model import ArnheimModel


def parse_kwargs(kwargs):

    parsed_kwargs = {}

    for key, value in kwargs.items():
        if isinstance(value, ArnheimModel):
            assert value.id is not None, "Cannot parse a ArnheimModel as Argument if it doesn't provide an ID"
            parsed_kwargs[key] = value.id
        else:
            parsed_kwargs[key] = value


    return parsed_kwargs