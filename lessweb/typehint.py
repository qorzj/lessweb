from typing import Type, Tuple
from typing_inspect import get_args, is_optional_type, is_generic_type, get_origin  # type: ignore


__all__ = ["optional_core", "generic_core", "is_optional_type", "is_generic_type", "get_origin"]


def optional_core(t: Type) -> Tuple[bool, Type]:
    """
    :return  (is_optional, t.core | t | NoneType)
    """
    if t is type(None):
        return True, type(None)
    if is_optional_type(t):
        first, second = get_args(t)
        return True, (second if isinstance(None, first) else first)
    else:
        return False, t


def generic_core(t: Type):
    args = get_args(t)
    return args[0]
