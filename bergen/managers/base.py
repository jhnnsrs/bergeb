

from bergen.query import TypedGQL


class ModelConfigurationError(Exception):
    pass


class BaseManager:

    def _call_meta(self, attribute, ward=None, **kwargs):
        method =  getattr(self.meta, attribute, None)
        assert method is not None, f"Please provide the {attribute} parameter in your ArnheimModel meta class for SchemaClass {self.model.__name__} "
        typed_gql: TypedGQL = method(self.model)    
        return typed_gql.run(ward=ward, variables=kwargs)
