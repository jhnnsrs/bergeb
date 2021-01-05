import re
from typing import Generator, Generic, Type, TypeVar



gqlparsed_with_variables = re.compile(r"[\s]*(?P<type>subscription|query|mutation)\s*(?P<operation>[a-zA-Z]*)\((?P<arguments>[^\)]*)\)[\s]*{[\s]*(?P<firstchild>[^\(:]*).*")
gqlparser_without_variables = re.compile(r"[\s]*(?P<type>subscription|query|mutation)\s*(?P<operation>[a-zA-Z]*)[\s]*{[\s]*(?P<firstchild>[^\(\{\s:]*).*")

class GQLException(Exception):
    pass


MyType = TypeVar("MyType")


class GQL(object):

    def __init__(self, query: str) -> None:
        self.query = query
        self.variables = None
        self._type = None
        self.m = gqlparsed_with_variables.match(self.query)
        self.has_variables = True
        if not self.m:
            self.m = gqlparser_without_variables.match(self.query)
            self.has_variables = False
            if not self.m:
                raise GQLException("Illformed request")

    def combine(self, variables: dict):
        self.variables = variables
        return {"query": self.query, "variables": self.variables}
        
    def parsed(self):
        assert self.variables and self.query, "Please specify query and set variables before parsing"
        return {"query": self.query, "variables": self.variables}

    @property
    def firstchild(self):
        return self.m.group("firstchild")

    @property
    def operation_name(self):
        return self.m.group("operation")

    @property
    def type(self):
        return self.m.group("type")

    def extract(self, result: dict):
        return result["data"][self.firstchild]



class QueryList(list):


     def _repr_html_(self) -> str:
        listified = list(self)
        string = "Result List with <br/><table>"
        for x, item in enumerate(listified):
             string += f"""
                <tr>
                    <td>{x}<td/>
                    <td>{item._repr_list_() if hasattr(item,"_repr_list_") else str(item)}</td>
                </tr>

            """
        string + "</table>"
        return string


    
class TypedGQL(GQL, Generic[MyType]):

    def __init__(self, query: str, cls: Type[MyType], aslist=False):
        self.aslist = aslist
        self.query = query
        self._cls = cls
        super().__init__(query)

    @property
    def cls(self) -> MyType:
        return self._cls


    def run(self, ward=None, **kwargs) -> MyType:
        from bergen.registries.arnheim import get_current_arnheim
        ward = ward or get_current_arnheim().getWard()
        returnedobject = ward.run(self, **kwargs)
        assert returnedobject is not None, "We received nothing back from the Server! Refine your Query!"
        if isinstance(returnedobject,list): return [self.cls(**item) for item in returnedobject]
        return self.cls(**returnedobject)


    def subscribe(self, ward=None, **kwargs) -> Generator[MyType, None,None]:
        from bergen.registries.arnheim import get_current_arnheim
        ward = ward or get_current_arnheim().getWard()
        return ward.subscribe(self, **kwargs)

    def _repr_html_(self) -> str:
        string = "Query <br/><table>"
        string + "</table>"
        return string


def DelayedGQL(gqlstring):
    return lambda model : TypedGQL(gqlstring, model)