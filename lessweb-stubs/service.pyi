from typing import Any


__all__ = ["Service"]


class Service:
    openapi_data: dict
    api_index: dict  # dict[op_id] -> [callback}]
    api_param_indx: dict  # dict[op_id] -> [{name, in, schema}]
    api_rev_index: dict  # dict[method, path] -> op_id
    api_schema_index: dict  # dict[op_id] -> schema
    resolver: Any

    def __init__(self, openapi_url): ...
    def endpoint(self, op_id): ...
    def response(self, request, context=None): ...
