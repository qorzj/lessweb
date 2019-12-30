from typing import *
from typing_inspect import *


__all__ = ["optional_core", "generic_core"]


NoneType = type(None)


def optional_core(t):
    """
    t is Optaional? t.core : NoneType
    >>> optional_core(List[int])
    <class 'NoneType'>
    >>> optional_core(Optional[str])
    <class 'str'>
    >>> optional_core(Union[int, str])
    <class 'NoneType'>
    """
    if is_optional_type(t) and t is not NoneType:
        first, second = get_args(t)
        return second if isinstance(None, first) else first
    else:
        return NoneType


def generic_core(t: Type):
    args = get_args(t)
    return args[0]
