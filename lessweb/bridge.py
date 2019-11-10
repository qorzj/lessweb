# 存放与类型转换有关的类型定义，且不依赖同级其他库
from typing import Type, TypeVar, get_type_hints, Any, Tuple, List, Callable, Union
from abc import abstractmethod, ABCMeta
from .typehint import issubtyping
from .utils import func_arg_spec
from .webapi import Jsonizable, ParamStr


class uint(int):
    pass


class RequestBridge:
    def __init__(self, bridge_funcs: List[Callable]):
        self.bridges: List[Callable] = bridge_funcs

    def cast(self, inputval: Union[ParamStr, Jsonizable], real_type: Type) -> Any:
        for bridge_func in self.bridges:
            dest_val = bridge_func(inputval, real_type)
            if dest_val is not None:
                return dest_val

        return self.default_cast(inputval, real_type)

    def default_cast(self, inputval: Union[ParamStr, Jsonizable], real_type: Type) -> Any:
        if real_type == bool and isinstance(inputval, ParamStr):
            if inputval.value == '✓': return True
            if inputval.value == '✗': return False
        if issubclass(real_type, int):
            n = int(inputval.value if isinstance(inputval, ParamStr) else inputval)
            if real_type == uint and n < 0:
                raise ValueError("invalid range for uint(): '%s'" % n)
            return real_type(n)
        return real_type(inputval.value if isinstance(inputval, ParamStr) else inputval)
