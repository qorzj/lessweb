from typing import Any, Tuple, Dict, Type, get_type_hints
from contextlib import contextmanager
import json
from pathlib import Path
import pickle
import re
import inspect


def eafp(ask, default):
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


def re_standardize(pattern):
    """
        >>> pattern = re_standardize('/add/{x}/{y}')
        >>> pattern
        '^/add/(?P<x>[0-9]+)/(?P<y>[0-9]+)$'

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
        return '(?P<%s>[0-9]+)' % x

    return re.sub(r'\{([^0-9].*?)\}', _repl, pattern)


def fields_in_query(query):
    """
        >>> fields_in_query('a=1&b=2')
        {'a': '1', 'b': '2'}

        >>> fields_in_query('')
        {}

        >>> fields_in_query('?')
        {}

    """
    ret = {}
    if query and query[0] == '?':
        query = query[1:]
    if not query:
        return ret
    for seg in query.split('&'):
        k, v = seg.split('=', 1)
        ret[k] = v
    return ret


class StaticDict(dict):
    touched = False

    def __delitem__(self, key):
        super().__delitem__(key)
        self.touched = True

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.touched = True

    def update(self, *E, **F):
        super().update(*E, **F)
        self.touched = True

    def pop(self, *k):
        ret = super().pop(*k)
        self.touched = True
        return ret


@contextmanager
def static_dict(path):
    is_json = path.lower().endswith('.json')
    path = Path(path)
    if is_json:
        data = StaticDict(json.load(path.open('r'))) if path.exists() else StaticDict()
    else:
        data = StaticDict(pickle.load(path.open('rb'))) if path.exists() else StaticDict()
    yield data
    if data.touched:
        path.parent.mkdir(parents=True, exist_ok=True)
        if is_json:
            json.dump(data, path.open('w'))
        else:
            pickle.dump(data, path.open('wb'))


def func_arg_spec(fn)->Dict[str, Tuple[Type, bool]]:
    arg_spec = {}  # name: (type_, has_default)
    inspect_ret = inspect.getfullargspec(fn)
    annotations = get_type_hints(fn)
    kw_len = len(inspect_ret.args) - len(inspect_ret.defaults or ())
    for i, name in enumerate(inspect_ret.args):
        arg_spec[name] = (annotations.get(name, Any), i >= kw_len)
    for name in inspect_ret.kwonlyargs:
        arg_spec[name] = (annotations.get(name, Any), True)
    return arg_spec


def makedir(real_path):
    Path(real_path).mkdir(parents=True, exist_ok=True)
