from typing import Optional
from pydantic.fields import Field
from pydantic.main import ModelMetaclass, BaseModel


class ObjectMetaClass(ModelMetaclass):

     def __new__(mcls, name, bases, attrs):
        
        slots = set(attrs.pop('__slots__', tuple())) # The slots from: https://github.com/samuelcolvin/pydantic/issues/655#issuecomment-610900376
        for base in bases:
            if hasattr(base, '__slots__'):
                slots.update(base.__slots__)

        if '__dict__' in slots:
            slots.remove('__dict__')
        attrs['__slots__'] = tuple(slots)

        mcls.overriden_manager = attrs.pop("objects") if "objects" in attrs else None
        mcls.overriden_async_manager = attrs.pop("asyncs") if "asyncs" in attrs else None
        return super(ObjectMetaClass, mcls).__new__(mcls, name, bases, attrs)



class ArnheimObject(BaseModel, metaclass=ObjectMetaClass):
    TYPENAME: str = Field(None, alias='__typename')

    def __repr__(self) -> str:
        from pprint import pformat
        return pformat(self.__dict__, indent=4, width=1)

    def _repr_html_(self):
        
        def buildTable(attributes):
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

    def __setattr__(self, attr, value):
        if attr in self.__slots__:
            object.__setattr__(self, attr, value)
        else:
            super().__setattr__(attr, value)