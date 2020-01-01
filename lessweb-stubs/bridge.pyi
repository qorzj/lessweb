from datetime import datetime as Datetime
from typing import Type, List, Callable, Union, Dict, Any


__all__ = ["uint", "Jsonizable", "ParamStr", "MultipartFile", "RequestBridgeFunc", "ResponseBridgeFunc"]


class uint(int): ...

Jsonizable = Union[str, int, float, Dict, List, None]

class ParamStr(str): ...

class MultipartFile:
    filename: str
    value: bytes
    def __init__(self, upfile): ...
    def __str__(self) -> str: ...


RequestBridgeFunc = Callable[[Union[ParamStr, Jsonizable], Type], Any]
ResponseBridgeFunc = Callable[[Any], Jsonizable]


def default_request_bridge(inputval: Union[ParamStr, Jsonizable], real_type: Type) -> Any: ...
def default_response_bridge(obj: Any) -> Jsonizable: ...


class RequestBridge:
    def __init__(self, bridge_funcs: List[RequestBridgeFunc]) -> None: ...
    def cast(self, inputval: Union[ParamStr, Jsonizable], real_type: Type) -> Any: ...


def make_response_encoder(bridge_funcs: List[ResponseBridgeFunc]): ...
