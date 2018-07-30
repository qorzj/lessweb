from contextlib import contextmanager
import json
from pathlib import Path
import pickle
import re
from typing import get_type_hints
from typing import TypeVar, Generic
from unittest.mock import Mock, DEFAULT
from .storage import Storage


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
_readonly = Nil(1)


T = TypeVar('T')
class Service(Generic[T]):
    ctx: T
    def __init__(self, ctx: T = None):
        self.ctx = ctx


def json_dumps(obj, encoders=()):

    class _1_Encoder(json.JSONEncoder):
        def default(self, obj):
            for f in encoders:
                t = get_type_hints(f)
                if 'return' in t: t.pop('return')
                assert len(t) == 1, repr(f) + ' in encoders expected 1 arguments with type hint'
                varclass = t.popitem()[1]
                if isinstance(obj, varclass):
                    return f(obj)
            return json.JSONEncoder.default(self, obj)

    return json.dumps(obj, cls=_1_Encoder)


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


class ChainMock:
    """
    Usage: https://github.com/qorzj/lessweb/wiki/%E7%94%A8mock%E6%B5%8B%E8%AF%95service
    """
    def __init__(self, path, return_value):
        self.returns = {}
        self.mock = {}
        self.join(path, return_value)

    def join(self, path, return_value):
        if not path.startswith('.'):
            path = '.' + path
        self.returns[path] = return_value
        self.mock[path] = Mock(return_value=return_value)
        while '.' in path:
            prefix, key = path.rsplit('.', 1)
            if prefix not in self.returns: self.returns[prefix] = Storage()
            self.returns[prefix][key] = self.mock[path]
            self.mock[prefix] = Mock(return_value=self.returns[prefix])
            path = prefix
        return self

    def __call__(self, path=None):
        if path is None:
            return self.mock['']()
        if not path.startswith('.'):
            path = '.' + path
        return self.mock[path]


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
