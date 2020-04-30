from typing import Type, Tuple
from typing_inspect import is_optional_type, is_generic_type, get_origin


__all__ = ["optional_core", "generic_core", "is_optional_type", "is_generic_type", "get_origin"]

is_optional_type = is_optional_type
is_generic_type = is_generic_type
get_origin = get_origin


def optional_core(t: Type) -> Tuple[bool, Type]:
def generic_core(t: Type) -> Type: ...
