import json
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
