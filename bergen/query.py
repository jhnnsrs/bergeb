import logging
import re
from typing import Generator, Generic, List, Type, TypeVar

logger = logging.getLogger(__name__)


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
        return result[self.firstchild]



class ListQuery(list):


    def __init__(self, *args, **kwargs):
        self._df = None
        super().__init__(*args, **kwargs)


    def to_df(self, exclude_unset=True, **kwargs):
        import pandas as pd
        if self._df is None: self._df = pd.json_normalize([rec.dict(exclude_unset=exclude_unset, **kwargs) for rec in self])
        return self._df

    def _repr_html_(self) -> str:
        return self.to_df().to_html()


    
class TypedGQL(GQL, Generic[MyType]):

    def __init__(self, query: str, cls: Type[MyType], aslist=False):
        self.aslist = aslist
        self.query = query
        self._cls = cls
        super().__init__(query)

    @property
    def cls(self) -> MyType:
        return self._cls

    async def run_async(self, ward=None, variables=None, **kwargs) -> MyType:
        ward = ward or self._cls.get_ward()
        returnedobject = await ward.run_async(self, variables=variables,**kwargs)
        assert returnedobject is not None, "We received nothing back from the Server! Refine your Query!"
        if isinstance(returnedobject,list): return ListQuery([self.cls(**item) for item in returnedobject])
        try:
            return self.cls(**returnedobject)
        except Exception as e:
            logger.error(returnedobject)
            raise e

    def run(self, ward=None, variables=None, **kwargs) -> MyType:
        ward = ward or self._cls.get_ward()
        returnedobject = ward.run(self, variables=variables, **kwargs)
        assert returnedobject is not None, "We received nothing back from the Server! Refine your Query!"
        if isinstance(returnedobject,list): return ListQuery([self.cls(**item) for item in returnedobject])
        return self.cls(**returnedobject)

    def subscribe(self, ward=None, **kwargs) -> Generator[MyType, None,None]:
        ward = ward or self._cls.get_ward()
        return ward.subscribe(self, **kwargs)

    def _repr_html_(self) -> str:
        string = "Query <br/><table>"
        string + "</table>"
        return string


class Query(GQL, Generic[MyType]):

    def __init__(self, query: str, cls: Type[MyType], aslist=False):
        self.aslist = aslist
        self.query = query
        self._cls = cls
        super().__init__(query)

    @property
    def cls(self) -> MyType:
        return self._cls

    def run(self, ward=None, variables=None, **kwargs) -> MyType:
        ward = ward or self._cls.get_ward()
        returnedobject = ward.run(self, variables=variables,**kwargs)
        if isinstance(returnedobject,list): raise Exception("Received a freaking list..., Please run QueryList")
        if not isinstance(returnedobject, dict):
            return self.cls(returnedobject) if returnedobject else None
        return self.cls(**returnedobject) if returnedobject else None

    def subscribe(self, ward=None, **kwargs) -> Generator[MyType, None,None]:
        ward = ward or self._cls.get_ward()
        return ward.subscribe(self, **kwargs)

    def _repr_html_(self) -> str:
        string = "Query <br/><table>"
        string + "</table>"
        return string


class QueryList(GQL, Generic[MyType]):

    def __init__(self, query: str, cls: Type[MyType], aslist=False):
        self.aslist = aslist
        self.query = query
        self._cls = cls
        super().__init__(query)

    @property
    def cls(self) -> MyType:
        return self._cls

    def run(self, ward=None, variables=None, **kwargs) -> List[MyType]:
        ward = ward or self._cls.get_ward()
        returnedobject = ward.run(self, variables=variables, **kwargs)
        return ListQuery([self.cls(**item) for item in returnedobject]) if returnedobject else ListQuery([])

    def subscribe(self, ward=None, **kwargs) -> Generator[List[MyType], None,None]:
        ward = ward or self._cls.get_ward()
        return ward.subscribe(self, **kwargs)

    def _repr_html_(self) -> str:
        string = "Query <br/><table>"
        string + "</table>"
        return string

class AsyncQuery(GQL, Generic[MyType]):

    def __init__(self, query: str, cls: Type[MyType], aslist=False):
        self.aslist = aslist
        self.query = query
        self._cls = cls
        super().__init__(query)

    @property
    def cls(self) -> MyType:
        return self._cls

    async def run(self, ward=None, variables=None, **kwargs) -> MyType:
        ward = ward or self._cls.get_ward()
        returnedobject = await ward.run_async(self, variables=variables,**kwargs)
        if isinstance(returnedobject,list): raise Exception("Received a freaking list..., Please run QueryList")
        if not isinstance(returnedobject, dict):
            return self.cls(returnedobject) if returnedobject else None
        return self.cls(**returnedobject) 

    def subscribe(self, ward=None, **kwargs) -> Generator[MyType, None,None]:
        ward = ward or self._cls.get_ward()
        return ward.subscribe(self, **kwargs)

    def _repr_html_(self) -> str:
        string = "Query <br/><table>"
        string + "</table>"
        return string

class AsyncQueryList(GQL, Generic[MyType]):

    def __init__(self, query: str, cls: Type[MyType], aslist=False):
        self.aslist = aslist
        self.query = query
        self._cls = cls
        super().__init__(query)

    @property
    def cls(self) -> MyType:
        return self._cls

    async def run(self, ward=None, variables=None, **kwargs) -> List[MyType]:
        ward = ward or self._cls.get_ward()
        returnedobject = await ward.run_async(self, variables=variables,**kwargs)
        return ListQuery([self.cls(**item) for item in returnedobject]) if returnedobject else ListQuery([])

    def subscribe(self, ward=None, **kwargs) -> Generator[MyType, None,None]:
        ward = ward or self._cls.get_ward()
        return ward.subscribe(self, **kwargs)

    def _repr_html_(self) -> str:
        string = "Query <br/><table>"
        string + "</table>"
        return string

def DelayedGQL(gqlstring):
    return lambda model : TypedGQL(gqlstring, model)




