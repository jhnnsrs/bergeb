from typing import Optional
from pydantic.fields import Field
from pydantic.main import ModelMetaclass, BaseModel



class ArnheimObject(BaseModel, metaclass=ModelMetaclass):
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