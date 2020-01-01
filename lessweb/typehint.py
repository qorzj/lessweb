from typing import Type
from typing_inspect import get_args, is_optional_type, is_generic_type, get_origin  # type: ignore


__all__ = ["optional_core", "generic_core", "is_optional_type", "is_generic_type", "get_origin"]


def optional_core(t):
    """
    t is Optaional? t.core : NoneType
    """
    if is_optional_type(t) and t is not None.__class__:
        first, second = get_args(t)
        return second if isinstance(None, first) else first
    else:
        return None.__class__


def generic_core(t: Type):
    args = get_args(t)
    return args[0]
