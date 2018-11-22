import inspect
from abc import ABCMeta
from enum import Enum
from inspect import _empty
from typing import *

from lessweb.context import Context
from lessweb.utils import _nil, _readonly
from lessweb.webapi import NeedParamError, BadParamError


class Model(metaclass=ABCMeta):
    pass


class Service(metaclass=ABCMeta):
    pass


Jsonizable = Union[str, int, bool, Dict, List, None]


def deprecated_func_parameters(func):
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


def deprecated_get_annotations(x):
    return getattr(x, '__annotations__', {})


def deprecated_get_model_parameters(cls):
    """get_model_parameters(Class) -> [(realname, Type, default), ...]"""
    annos = deprecated_get_annotations(cls)
    inst = cls()
    defaults = {
        k: getattr(inst, k, _nil) for k in cls.__dict__
    }
    for k in cls.__dict__:  # handle read-only property
        if isinstance(getattr(cls, k), property) and not getattr(cls, k).fset:
            defaults[k] = _readonly

    return [
        (k, annos.get(k, _nil), defaults.get(k, _nil))  # (realname, Type, default)
        for k in
        (lambda x, y: x.update(y) or x)(annos.copy(), defaults)
        if k[0] != '_'
    ]


def deprecated_input_by_choose(ctx: Context, fn, realname, realtype, default):
    """

        >>> def foo(a, b, c=0, d=1, e=2):
        ...     pass
        >>> ctx = Context()
        >>> ctx._fields = dict(a='A', b='B', c='C', d='D', e='E', f='F')
        >>> ctx.querynames = 'a,b,c'
        >>> [input_by_choose(ctx, foo, k, realtype=str, default=None) for k in 'abcde']
        ['A', 'B', 'C', None, None]
    """
    queryname = ctx.aliases.get(realname, realname)

    if realname in ctx._pipe:
        value = ctx.get_param(realname)
    else:
        pre_value = ctx.get_input(queryname, default=_nil)
        try:
            if pre_value != _nil:
                if not isinstance(realtype, type):
                    value = realtype(pre_value)
                elif not issubclass(realtype, RestParam):
                    if realtype is int:
                        value = max(int(pre_value), 0)
                    elif issubclass(realtype, Enum):
                        def _eval_enum(x, T):
                            for e in T.__members__.values():
                                if str(e.value) == str(x):
                                    return e
                            raise ValueError("%r is not a valid %s" % (x, T.__name__))

                        value = _eval_enum(pre_value, realtype)
                    else:
                        value = realtype(pre_value)
                else:  # realtype is subclass of RestParam
                    value = realtype()
                    if ctx.is_json_request():
                        if hasattr(value, 'lessweb_eval_from_json'):
                            value.lessweb_eval_from_json(pre_value)
                        else:
                            value.eval_from_json(pre_value)
                    else:  # ctx is not json request
                        if hasattr(value, 'lessweb_eval_from_text'):
                            value.lessweb_eval_from_text(pre_value)
                        else:
                            value.eval_from_text(pre_value)

            else:  # pre_value == _nil
                value = _nil
        except (ValueError, TypeError) as e:
            raise BadParamError(query=queryname, error=str(e))

    if value == _nil:
        if default == _nil:
            raise NeedParamError(query=queryname, doc=queryname)
        return default
    else:
        return value


def deprecated_fetch_model_param(ctx: Context, cls, fn):
    """

        >>> class Person(Model):
        ...     name: str
        ...     age: int
        ...     weight: int
        >>> def get_person(ctx, person: Person): pass
        >>> ctx = Context()
        >>> ctx.set_alias('weight', 'w')
        >>> ctx._fields = dict(name='Bob', age='33', w='100', x='1')
        >>> model = fetch_model_param(ctx, Person, get_person)
        >>> assert model.storage() == {'name': 'Bob', 'age': 33, 'weight': 100}, model.items()
    """
    result = {}
    for realname, realtype, default in get_model_parameters(cls):
        if default == _readonly:
            continue
        if realtype == _nil:
            realtype = str
        value = input_by_choose(ctx, fn, realname, realtype, default)
        result[realname] = value
    model = cls()
    model.setall(**result)
    return model


def deprecated_fetch_param(ctx: Context, fn):
    """
        >>> def get_person(ctx:Context, name:str, age:int, weight:int, createAt:int=2):
        ...     pass
        >>> ctx = Context()
        >>> ctx.querynames = 'name,age,weight'
        >>> ctx.set_alias('weight', 'w')
        >>> ctx._fields = dict(name='Bob', age='33', w='100', weight='1', createAt='9')
        >>> param = fetch_param(ctx, get_person)
        >>> assert param == {'ctx': ctx, 'name': 'Bob', 'age': 33, 'weight': 100, 'createAt': 2}, param
    """
    result = {}
    for realname, realtype, default in get_func_parameters(fn):
        if isinstance(realtype, type):
            if issubclass(realtype, Context):
                result[realname] = ctx
                continue

            if issubclass(realtype, Service):
                result[realname] = realtype(ctx)
                continue

            if issubclass(realtype, Model):
                result[realname] = fetch_model_param(ctx, realtype, fn)
                continue

        if realtype == _nil: realtype = str
        value = input_by_choose(ctx, fn, realname, realtype, default)
        result[realname] = value

    return result
