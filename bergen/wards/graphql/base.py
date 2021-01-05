from abc import ABC
import re
from bergen.wards.base import BaseWard
from bergen.query import GQL, TypedGQL
import requests


class GraphQlException(Exception):
    pass

class ProtocolException(GraphQlException):
    pass

class SyntaxException(GraphQlException):
    pass

class QueryException(GraphQlException):
    pass


class BaseGraphQLWard(BaseWard, ABC):
    can_subscribe = False
    

    def __init__(self, port=8000, host="localhost", protocol="http", token=None) -> None:
        self._graphql_endpoint = f"{protocol}://{host}:{port}/graphql"
        self._token = token
        self._headers = {"Authorization": f"Bearer: {self._token}"}
        super().__init__(port=port, host=host, protocol=protocol, token=token)


    def post(self, json, url = None, headers = None):
        request = requests.post(url or self._graphql_endpoint, json=json, headers= headers or self._headers)
        if request.status_code == 200:
            result = request.json()
            if "errors" in result:
                raise QueryException(",".join([error["message"] for error in result["errors"]]))
            return result

        if request.status_code == 400:
            result = request.json()
            if "errors" in result:
                raise QueryException(",".join([error["message"] for error in result["errors"]]))
                
        else:
            raise ProtocolException(f"Post failed to run by returning code of {request.status_code}. {request.content}")

    def run(self, gql: TypedGQL, variables: dict = {}):
        result = self.post(gql.combine(variables))
        return gql.extract(result)