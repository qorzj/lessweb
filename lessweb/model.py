from enum import Enum as DefaultEnum
import inspect
from inspect import _empty
from typing import *

from lessweb.context import Context
from lessweb.sugar import _nil
from lessweb.webapi import NeedParamError, BadParamError


class RestParam:
    def __init__(self, getter=str, jsongetter=None, default=None, queryname=None, doc=''):
        self.getter: Callable = getter  # 用于从str获取值
        self.jsongetter: Optional[Callable] = jsongetter  # 用于从json获取值
        self.default: Any = default
        self.queryname: Optional[str] = queryname  # 用于指定前端使用的名称
        self.doc: str = doc


def tips(slot: str):
    """
        >>> @tips('st')
        ... def tag(x):
        ...     return x + x
        >>> @tag(5)
        ... @tag(3)
        ... def f():
        ...     pass
        >>> assert f.__tips__['st'] == [6, 10]
    """
    def g(fn):
        def f(*a, **b):
            tip_value = fn(*a, **b)
            def h(foo):
                if not hasattr(foo, '__tips__'):
                    foo.__tips__ = {}
                foo.__tips__.setdefault(slot, [])
                foo.__tips__[slot].append(tip_value)
                return foo
            return h
        return f
    return g


@tips('rest-param')
def rest_param(key, *, getter=str, jsongetter=None, default=None, queryname=None, doc=None):
    """
    >>> @rest_param('x')
    ... def foo(x): pass
    >>> a: RestParam = foo.__tips__['rest-param']
    >>> assert (a.getter, a.jsongetter, a.default, a.queryname, a.doc) == (str, None, None, 'x', 'x')
    """
    if doc is None: doc = key
    if queryname is None: queryname = key
    return key, RestParam(getter, jsongetter, default, queryname, doc)


@tips('choose-param')
def need_param(*keys):
    return 'need', keys


@tips('choose-param')
def choose_param(*keys):
    return 'choose', keys


@tips('choose-param')
def unchoose_param(*keys):
    return 'unchoose', keys


@tips('enum-show')
def enum_show(mapping):
    return mapping


class Enum(DefaultEnum):
    """
    >>> @enum_show({1: 'Red', 2: 'Green'})
    ... class Color(Enum):
    ...     R = 1
    ...     G = 2
    >>> assert Color.R.show() == 'Red'
    >>> assert Color(2).show() == 'Green'
    """
    def show(self):
        mapping = get_tips(self, 'enum-show')
        if not mapping:
            return self.name
        else:
            return mapping[0][self.value]


def get_func_parameters(func):
    """
    >>> def f(a:int, b=4)->int:
    ...   return a+b
    >>> ret = get_func_parameters(f)
    >>> assert ret == [('a', int, _nil), ('b', _nil, 4)]
    """
    return [
        (
            p,
            _nil if q.annotation is _empty else q.annotation ,
            _nil if q.default is _empty else q.default,
        )
        for p, q in inspect.signature(func).parameters.items()
    ]


def get_tips(fn, slot: str):
    return getattr(fn, '__tips__', {}).get(slot, [])


def get_annotations(x):
    return getattr(x, '__annotations__', {})


def get_model_parameters(cls):
    annos = get_annotations(cls)
    inst = cls()
    defaults = {
        k: getattr(inst, k, _nil) for k in cls.__dict__
    }
    return [
        (k, annos.get(k, _nil), defaults.get(k, _nil))
        for k in
        (lambda x, y: x.update(y) or x)(annos.copy(), defaults)
        if k[0] != '_'
    ]


class Model:
    def setall(self, **kwargs):
        for k, v in kwargs.items():
            if k[0] != '_':
                setattr(self, k, v)

    def items(self):
        return {
            k: getattr(self, k) for k, _, _
            in get_model_parameters(type(self))
            if hasattr(self, k)
        }

    def copy(self, **kwargs):
        ret = self.__class__()
        ret.setall(**self.items())
        ret.setall(**kwargs)
        return ret

    def __eq__(self, other):
        return self is other or (type(self) == type(other) and self.items() == other.items())

    def __repr__(self):
        return '<Model ' + repr(self.items()) + '>'


def input_by_choose(ctx: Context, fn, key, rest_param: RestParam):
    """

        >>> @need_param('a', 'b')
        ... @choose_param('c', 'd')
        ... @unchoose_param('d', 'e')
        ... def foo(a, b, c=0, d=1, e=2):
        ...     pass
        >>> ctx = Context()
        >>> ctx._fields = dict(a='A', b='B', c='C', d='D', e='E', f='F')
        >>> [input_by_choose(ctx, foo, k, RestParam()) for k in 'abcde']
        ['A', 'B', 'C', None, None]
    """
    chooseparam_tips = {k:v for k,v in get_tips(fn, 'choose-param')}
    if ctx.is_json_request():
        getter = rest_param.jsongetter or rest_param.getter
    else:
        getter = rest_param.getter
    queryname = rest_param.queryname or key
    value = ctx.get_input(queryname, default=_nil)
    keys_will_choose = chooseparam_tips.get('choose', None)
    if getter is None:
        return rest_param.default

    if key in chooseparam_tips.get('need', []):
        if value is _nil:
            raise NeedParamError(query=queryname, doc=rest_param.doc)
    elif key in chooseparam_tips.get('unchoose', []) or \
            (keys_will_choose is not None and key not in keys_will_choose):
        return rest_param.default

    if value is _nil:
        return rest_param.default
    try:
        return getter(value)
    except (ValueError, TypeError) as e:
        raise BadParamError(query=queryname, error=str(e))


def fetch_model_param(ctx: Context, cls, fn):
    """

        >>> @rest_param('weight', getter=int, queryname='w')
        ... class Person(Model):
        ...     name: str
        ...     age: int
        ...     weight = None
        >>> def get_person(ctx, person: Person): pass
        >>> ctx = Context()
        >>> ctx._fields = dict(name='Bob', age='33', w='100', x='1')
        >>> model = fetch_model_param(ctx, Person, get_person)
        >>> assert model.items() == {'name': 'Bob', 'age': 33, 'weight': 100}, model.items()
    """
    restparam_tips = {k:v for k,v in get_tips(cls, 'rest-param')}
    result = {}
    for key, anno, default in get_model_parameters(cls):
        if key in ctx.pipe:
            result[key] = ctx.pipe[key]
            continue

        if key in restparam_tips:
            param = restparam_tips[key]
        else:
            if anno is _nil: vartype = str
            elif anno is int: vartype = lambda x: max(int(x), 0)
            elif issubclass(anno, DefaultEnum): vartype = lambda x: anno(int(x))
            else: vartype = anno
            default = None if default is _nil else default
            param = RestParam(getter=vartype, default=default, doc=key)

        value = input_by_choose(ctx, fn, key, param)
        result[key] = value
    model = cls()
    model.setall(**result)
    return model


def fetch_param(ctx: Context, fn):
    """

        >>> @rest_param('weight', getter=int, queryname='w')
        ... def get_person(ctx, name: str, age: int, weight):
        ...     pass
        >>> ctx = Context()
        >>> ctx._fields = dict(name='Bob', age='33', w='100', weight='1')
        >>> param = fetch_param(ctx, get_person)
        >>> assert param == {'name': 'Bob', 'age': 33, 'weight': 100}, param
    """
    restparam_tips = {k:v for k,v in get_tips(fn, 'rest-param')}
    result = {}
    for key, anno, default in get_func_parameters(fn)[1:]:
        if key in ctx.pipe:
            result[key] = ctx.pipe[key]
            continue

        if isinstance(anno, type) and issubclass(anno, Model):
            result[key] = fetch_model_param(ctx, anno, fn)
            continue

        if key in restparam_tips:
            param = restparam_tips[key]
        else:
            if anno is _nil: vartype = str
            elif anno is int: vartype = lambda x: max(int(x), 0)
            elif issubclass(anno, DefaultEnum): vartype = lambda x: anno(int(x))
            else: vartype = anno
            default = None if default is _nil else default
            param = RestParam(getter=vartype, default=default, doc=key)

        value = input_by_choose(ctx, fn, key, param)
        result[key] = value
    return result