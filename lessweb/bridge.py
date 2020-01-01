# 存放与类型转换有关的类型定义，且不依赖同级其他库
from enum import Enum
from datetime import datetime as Datetime
from json import JSONEncoder
from itertools import chain
from typing import Type, List, Callable, Union, Dict, Any
from .storage import Storage


__all__ = ["uint", "Jsonizable", "ParamStr", "MultipartFile", "RequestBridgeFunc", "ResponseBridgeFunc"]


class uint(int):
    pass


Jsonizable = Union[str, int, float, Dict, List, None]


class ParamStr(str):
    pass


class MultipartFile:
    filename: str
    value: bytes

    def __init__(self, upfile):
        self.filename = upfile.filename
        self.value = upfile.value

    def __str__(self) -> str:
        return f'<MultipartFile filename={self.filename} value={str(self.value)}>'


RequestBridgeFunc = Callable[[Union[ParamStr, Jsonizable], Type], Any]
ResponseBridgeFunc = Callable[[Any], Jsonizable]


def default_request_bridge(inputval: Union[ParamStr, Jsonizable], real_type: Type) -> Any:
    if real_type == bool and isinstance(inputval, ParamStr):
        if inputval == '✓': return True
        if inputval == '✗': return False
    if issubclass(real_type, int):
        if isinstance(inputval, Dict) or isinstance(inputval, List) or inputval is None:
            raise ValueError("invalid input value for int(): '%s'" % inputval)
        n = int(inputval)
        if real_type == uint and n < 0:
            raise ValueError("invalid range for uint(): '%s'" % n)
        return real_type(n)
    if type(inputval) is real_type:
        return inputval
    else:
        return real_type(inputval)


def default_response_bridge(obj: Any) -> Jsonizable:
    if isinstance(obj, Datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    return None


class RequestBridge:
    def __init__(self, bridge_funcs: List[RequestBridgeFunc]):
        self.bridges: List[Callable] = bridge_funcs

    def cast(self, inputval: Union[ParamStr, Jsonizable], real_type: Type) -> Any:
        for bridge_func in self.bridges:
            dest_val = bridge_func(inputval, real_type)
            if dest_val is not None:
                return dest_val

        return default_request_bridge(inputval, real_type)


def make_response_encoder(bridge_funcs: List[ResponseBridgeFunc]):
    class ResponseEncoder(JSONEncoder):
        def default(self, obj):
            if obj is None:
                return obj
            for bridge_func in chain(bridge_funcs, [default_response_bridge]):
                dest_val = bridge_func(obj)
                if dest_val is not None:
                    return dest_val
            try:
                return Storage.of(obj)
            except:
                return str(obj)

    return ResponseEncoder
