import sys
from typing import Any, Tuple, Dict, Type, get_type_hints, Callable
from contextlib import contextmanager
import json
from pathlib import Path
import pickle
import re
import inspect
from inspect import Signature


__all__ = ["eafp", "_nil", "re_standardize", "func_arg_spec", "makedir"]
NEW_INSPECT = sys.version_info[:3] >= (3, 8, 0)


def eafp(ask: Callable, default: Any) -> Any:
    """
    Easier to ask for forgiveness than permission
    `x = eafp(lambda: int('a'), 0)` is equivalent to `x = int('a') ?? 0`
    """
    try:
        return ask()
    except:
        return default


class Nil:
    def __init__(self, value):
        self.value = value

    def __bool__(self):
        return False

    def __eq__(self, other):
        return isinstance(other, Nil) and self.value == other.value


_nil = Nil(0)


def re_standardize(pattern: str) -> str:
    """
        >>> pattern = re_standardize('/add/{x}/{y}')
        >>> pattern
        '^/add/(?P<x>[^/]+)/(?P<y>[^/]+)$'
        >>> re.search(pattern, '/add/234/5').groupdict()
        {'x': '234', 'y': '5'}
        >>> re.search(pattern, '/add//add') is None
        True
        >>> re.search(pattern, '/add/1/2/') is None
        True

    """
    if not pattern:
        return '^$'
    if pattern[0] != '^':
        pattern = '^' + pattern
    if pattern[-1] != '$':
        pattern = pattern + '$'
    def _repl(obj):
        x = obj.groups()[0]
        return '(?P<%s>[^/]+)' % x

    return re.sub(r'\{([^0-9].*?)\}', _repl, pattern)


def func_arg_spec(fn: Any) -> Dict[str, Tuple[Type, bool, bool]]:
    empty = Signature.empty
    arg_spec = {}  # name: (type_, has_default, positional-only)
    for name, param in inspect.signature(fn).parameters.items():
        arg_spec[name] = (
            Any if param.annotation is empty else param.annotation,
            param.default is not empty,
            NEW_INSPECT and param.kind == 0
        )
    return arg_spec


def makedir(real_path: str) -> None:
    Path(real_path).mkdir(parents=True, exist_ok=True)
