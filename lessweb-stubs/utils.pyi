from typing import Any, Tuple, Dict, Type, get_type_hints
from contextlib import contextmanager
import json
from pathlib import Path
import pickle
import re
import inspect


def eafp(ask, default): ...


class Nil:
    def __init__(self, value) -> None: ...
    def __bool__(self): ...
    def __eq__(self, other): ...


_nil: Nil = ...
def re_standardize(pattern) -> str: ...
def fields_in_query(query) -> Dict: ...


class StaticDict(dict):
    touched: bool
    def __delitem__(self, key): ...
    def __setitem__(self, key, value): ...
    def update(self, *E, **F) -> None: ...
    def pop(self, *k) -> None: ...


@contextmanager
def static_dict(path): ...
def func_arg_spec(fn)->Dict[str, Tuple[Type, bool]]: ...
def makedir(real_path: str) -> None: ...
