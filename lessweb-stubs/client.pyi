from typing import Any


__all__ = ["Client"]


class Client:
    api_index: dict  # dict[op_id] -> (method, path)
    api_param_indx: dict  # dict[op_id] -> [{name, in}]
    base_url: str
    token: str
    req_data: dict
    resp_data: Any

    def __init__(self, openapi_url, base_url): ...
    def login(self, token: str): ...
    def logout(self): ...
    def request(self, op_id, params=None, body=None, expect=200): ...
    def check(self): ...
