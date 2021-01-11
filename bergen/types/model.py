from abc import ABC, abstractmethod
from bergen.managers.base import BaseManager
from bergen.types.manager import ModelManager
from typing import Callable, Dict, Generic, List, TypeVar, Type
from pydantic.fields import Field
from pydantic.main import BaseModel, ModelMetaclass
from bergen.query import DelayedGQL, GQL, TypedGQL

class ArnheimModelException(Exception):
    pass

class ModelDoesNotExistError(ArnheimModelException):
    pass

class ArnheimModelConfigurationError(ArnheimModelException):
    pass


ModelType = TypeVar("ModelType", bound="ArnheimModel", covariant=True)

class ArnheimModelManager(BaseManager, Generic[ModelType]):

    def __init__(self, model: ModelType, meta) -> None:
        self.model = model
        self.meta = meta
        super().__init__()

    def get_ward(self):
        try:
            identifier = self.model.Meta.identifier
        except Exception as e:
            raise ArnheimModelConfigurationError(f"Make soure your Model {self.model.__name__}overwrites Meta identifier: {e}")
        from bergen.registries.arnheim import get_current_arnheim


        return get_current_arnheim().getWardForIdentifier(identifier=identifier)


    def _call_meta(self, attribute, ward=None, **kwargs):
        method =  getattr(self.meta, attribute, None)
        assert method is not None, f"Please provide the {attribute} parameter in your ArnheimModel meta class "
        typed_gql: TypedGQL = method(self.model)    
        return typed_gql.run(ward=ward, variables=kwargs)


    def get(self, ward=None, **kwargs) -> ModelType:
        return self._call_meta("get", ward=ward, **kwargs)
        
    def create(self, ward=None, **kwargs) -> ModelType:
        return self._call_meta("create", ward=ward, **kwargs)

    def filter(self, ward=None, **kwargs) -> List[ModelType]:
        return self._call_meta("filter", ward=ward, **kwargs)

    def update(self, ward=None, **kwargs) -> ModelType:
        return self._call_meta("update", ward=ward, **kwargs)

    def all(self, ward=None):
        return self._call_meta("filter", ward=ward)



class ArnheimModelMeta(ModelMetaclass):

    def __new__(mcls, name, bases, attrs):
        
        slots = set(attrs.pop('__slots__', tuple())) # The slots from: https://github.com/samuelcolvin/pydantic/issues/655#issuecomment-610900376
        for base in bases:
            if hasattr(base, '__slots__'):
                slots.update(base.__slots__)

        if '__dict__' in slots:
            slots.remove('__dict__')
        attrs['__slots__'] = tuple(slots)

        mcls.overriden_manager = attrs.pop("objects") if "objects" in attrs else None
        return super(ArnheimModelMeta, mcls).__new__(mcls, name, bases, attrs)


    @property
    def objects(cls: Type[ModelType]) -> ArnheimModelManager[ModelType]:
        return cls.__objects


    def __init__(self, name, bases, attrs):
        super(ArnheimModelMeta, self).__init__(name, bases, attrs)
        if attrs["__qualname__"] != "ArnheimModel":
            # This gets allso called for our Baseclass which is abstract
            meta = attrs["Meta"] if "Meta" in attrs else None
            assert meta is not None, "Please provide a Meta class in your Arnheim Model"
            
            managerClass = self.overriden_manager
            if managerClass:
                self.__objects = managerClass(self, meta)
            else:
                self.__objects = ArnheimModelManager[ModelType](self, meta)


            
            overwriteType = getattr(meta, "overwrite_default", False)
            register = getattr(meta, "register", True)
            if register:
                from bergen.registries.matcher import get_current_matcher
                identifier = getattr(meta, "identifier", None)
                assert identifier is not None, "Please provide identifier in your Meta class to register the Model, or specifiy register==False"
                get_current_matcher().registerModelForIdentifier(identifier, self, overwrite=overwriteType)






class ArnheimModel(BaseModel, metaclass=ArnheimModelMeta):
    TYPENAME: str = Field(None, alias='__typename')


    @classmethod
    def getMeta(cls):
        return cls.Meta

    def __repr__(self) -> str:
        from pprint import pformat
        return pformat(self.__dict__, indent=4, width=1)

    def _repr_html_(self):
        
        def buildTable(attributes: Dict):
            tablestring = "<table>"
            for key, value in attributes.items():
                tablestring = tablestring + (f"""
                    <tr>
                        <td>{key.capitalize()}</td>
                        <td>{value}</td>
                    </tr>
                """)
            return tablestring + "</table>"



        return f"""
            <p> Instance of {self.__class__.__name__} <p>
            {buildTable(self.__dict__)}
        """

    def _repr_list_(self):
        string = f"{self.__class__.__name__}("
        if self.id is not None: string += str(self.id) + ", "
        if self.name is not None: string += str(self.name) +", "
        string = string[:-2] + ")"
        return string


    def __setattr__(self, attr, value):
        if attr in self.__slots__:
            object.__setattr__(self, attr, value)
        else:
            super().__setattr__(attr, value)
