import json
import re
from typing import get_type_hints


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
    def __bool__(self):
        return False


_nil = Nil()


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
        '^/add/(?P<x>[^/]*)/(?P<y>[^/]*)$'

        >>> re.search(pattern, '/add/234/5').groupdict()
        {'x': '234', 'y': '5'}
        >>> re.search(pattern, '/add//add').groupdict()
        {'x': '', 'y': 'add'}
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
        return '(?P<%s>[^/]*)' % x

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
