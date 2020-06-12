# 存放与类型转换有关的类型定义，且不依赖同级其他库
from enum import Enum
from datetime import datetime as Datetime
from json import JSONEncoder
from itertools import chain
from typing import Type, List, Callable, Union, Dict, Any
from .storage import Storage


__all__ = ["uint", "Jsonizable", "ParamStr", "MultipartFile", "JsonBridgeFunc"]


class uint(int):
    def __init__(self, v):
        super().__init__()
        if self < 0:
            raise ValueError("invalid range for uint(): '%d'" % self)


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


JsonBridgeFunc = Callable[[Any], Jsonizable]


def default_response_bridge(obj: Any) -> Jsonizable:
    if isinstance(obj, Datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, bytes):
        return str(obj)
    return None


def make_response_encoder(bridge_funcs: List[JsonBridgeFunc]):
    class ResponseEncoder(JSONEncoder):
        def default(self, obj):
            if obj is None:
                return obj
            for bridge_func in chain(bridge_funcs, [default_response_bridge]):
                dest_val = bridge_func(obj)
                if dest_val is not None:
                    return dest_val
            try:
                if Storage.type_hints(type(obj)):
                    return Storage.of(obj)
            except:
                pass

    return ResponseEncoder
