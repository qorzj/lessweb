from typing import Any, Tuple, Dict, Type, Callable


__all__ = ["eafp", "_nil", "re_standardize", "func_arg_spec", "makedir"]


def eafp(ask: Callable, default: Any) -> Any: ...


class Nil:
    def __init__(self, value): ...
    def __bool__(self) -> bool: ...
    def __eq__(self, other) -> bool: ...


_nil: Nil
def re_standardize(pattern: str) -> str: ...
def func_arg_spec(fn: Any) -> Dict[str, Tuple[Type, bool]]: ...
def makedir(real_path: str) -> None: ...
