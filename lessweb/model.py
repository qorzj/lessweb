import inspect
import functools
from enum import Enum
from inspect import _empty
from typing import *

from lessweb.context import Context
from lessweb.utils import _nil
from lessweb.webapi import NeedParamError, BadParamError
from lessweb.storage import Storage


class RestParam:
    def __init__(self, getter=str, jsongetter=None, default=None, queryname=None, doc='') -> None:
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
                @functools.wraps(foo)
                def goo(*p, **q):
                    return foo(*p, **q)

                if not hasattr(goo, '__tips__'):
                    goo.__tips__ = {}
                goo.__tips__.setdefault(slot, [])
                goo.__tips__[slot].append(tip_value)
                return goo
            return h
        return f
    return g


@tips('rest-param')
def rest_param(realname, *, getter=str, jsongetter=None, default=None, queryname=None, doc=None):
    """
    >>> @rest_param('x')
    ... def foo(x): pass
    >>> a: RestParam = foo.__tips__['rest-param']
    >>> assert (a.getter, a.jsongetter, a.default, a.queryname, a.doc) == (str, None, None, 'x', 'x')
    """
    if doc is None: doc = realname
    if queryname is None: queryname = realname
    return realname, RestParam(getter, jsongetter, default, queryname, doc)


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
    def storage(self):
        return Storage({
            k: getattr(self, k) for k, _, _
            in get_model_parameters(type(self))
            if hasattr(self, k)
        })

    def setall(self, *mapping, **kwargs):
        if mapping:
            self.setall(**mapping[0])
        for k, v in kwargs.items():
            if k[0] != '_':
                try:
                    setattr(self, k, v)
                except AttributeError:  # property without setter
                    pass

    def copy(self, *mapping, **kwargs):
        ret = self.__class__()
        ret.setall(**self.storage())
        if mapping:
            ret.setall(**mapping[0])
        ret.setall(**kwargs)
        return ret

    def __eq__(self, other):
        return self is other or (type(self) == type(other) and self.storage() == other.storage())

    def __repr__(self):
        return '<Model ' + repr(dict(self.storage())) + '>'


def input_by_choose(ctx: Context, fn, realname, rest_param: RestParam):
    """

        >>> def foo(a, b, c=0, d=1, e=2):
        ...     pass
        >>> ctx = Context()
        >>> ctx._fields = dict(a='A', b='B', c='C', d='D', e='E', f='F')
        >>> [input_by_choose(ctx, foo, k, RestParam()) for k in 'abcde']
        ['A', 'B', 'C', None, None]
    """
    if ctx.is_json_request():
        getter = rest_param.jsongetter or rest_param.getter
    else:
        getter = rest_param.getter
    queryname = rest_param.queryname or realname

    if realname in ctx._pipe:
        value = ctx.get_param(realname)
    else:
        pre_value = ctx.get_input(queryname, default=_nil)
        try:
            if getter is None:
                value = rest_param.default
            else:
                if pre_value is not _nil:
                    value = getter(pre_value)
                else:
                    value = _nil
        except (ValueError, TypeError) as e:
            raise BadParamError(query=queryname, error=str(e))

    if value is _nil or value is None:
        if rest_param.default is None:
            raise NeedParamError(query=queryname, doc=queryname)
        return rest_param.default
    else:
        return value


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
        >>> assert model.storage() == {'name': 'Bob', 'age': 33, 'weight': 100}, model.items()
    """
    restparam_tips = {k:v for k,v in get_tips(cls, 'rest-param')}
    result = {}
    for realname, anno, default in get_model_parameters(cls):
        if realname in restparam_tips:
            param = restparam_tips[realname]
        else:
            if anno is _nil: vartype = str
            elif anno is int: vartype = lambda x: max(int(x), 0)
            elif issubclass(anno, Enum): vartype = lambda x: anno(int(x))
            else: vartype = anno
            default = None if default is _nil else default
            param = RestParam(getter=vartype, default=default, doc=realname)

        value = input_by_choose(ctx, fn, realname, param)
        result[realname] = value
    model = cls()
    model.setall(**result)
    return model


def fetch_param(ctx: Context, fn):
    """

        >>> @rest_param('weight', getter=int, queryname='w')
        ... @rest_param('createAt', getter=None, default=2)
        ... def get_person(ctx, name: str, age: int, weight, createAt:int=8):
        ...     pass
        >>> ctx = Context()
        >>> ctx._fields = dict(name='Bob', age='33', w='100', weight='1', createAt='9')
        >>> param = fetch_param(ctx, get_person)
        >>> assert param == {'name': 'Bob', 'age': 33, 'weight': 100, 'createAt': 2}, param
    """
    restparam_tips = {k:v for k,v in get_tips(fn, 'rest-param')}
    result = {}
    for realname, anno, default in get_func_parameters(fn):
        if isinstance(anno, type) and issubclass(anno, Context):
            result[realname] = ctx
            continue

        if isinstance(anno, type) and issubclass(anno, Model):
            result[realname] = fetch_model_param(ctx, anno, fn)
            continue

        if realname in restparam_tips:
            param = restparam_tips[realname]
        else:
            if anno is _nil: vartype = str
            elif anno is int: vartype = lambda x: max(int(x), 0)
            elif issubclass(anno, Enum):
                def _enum_init(x, T=anno):
                    for e in T.__members__.values():
                        if str(e.value) == str(x):
                            return e
                    raise ValueError("%r is not a valid %s" % (x, T.__name__))

                vartype = _enum_init
            else: vartype = anno
            default = None if default is _nil else default
            param = RestParam(getter=vartype, default=default, doc=realname)

        value = input_by_choose(ctx, fn, realname, param)
        result[realname] = value
    return result