from datetime import datetime as Datetime
from typing import Type, List, Callable, Union, Dict, Any


__all__ = ["uint", "Jsonizable", "ParamStr", "MultipartFile", "JsonBridgeFunc"]


class uint(int): ...

Jsonizable = Union[str, int, float, Dict, List, None]

class ParamStr(str): ...

class MultipartFile:
    filename: str
    value: bytes
    def __init__(self, upfile): ...
    def __str__(self) -> str: ...


JsonBridgeFunc = Callable[[Any], Jsonizable]


def default_response_bridge(obj: Any) -> Jsonizable: ...
def make_response_encoder(bridge_funcs: List[JsonBridgeFunc]): ...
