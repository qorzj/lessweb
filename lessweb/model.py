from typing import Callable, Optional, Type, get_type_hints
from abc import ABCMeta

from lessweb.context import Context, Request, Response
from lessweb.webapi import NeedParamError, BadParamError, UploadedFile
from lessweb.typehint import generic_origin
from lessweb.garage import BaseBridge, Bridge, Jsonizable
from lessweb.utils import func_arg_spec
from lessweb.storage import Storage


class Model(metaclass=ABCMeta):
    def __eq__(self, other):
        return Storage.of(self) == Storage.of(other)

    def __repr__(self):
        return '<Model ' + repr(Storage.of(self)) + '>'


class Service(metaclass=ABCMeta):
    pass


def fetch_service(ctx: Context, service_type: Type):
    self_flag = True
    params = {}
    for realname, (realtype, _) in func_arg_spec(service_type.__init__).items():
        if self_flag or realname == 'return':
            self_flag = False
        elif realtype == Context:
            params[realname] = ctx
        elif realtype == Request:
            params[realname] = ctx.request
        elif realtype == Response:
            params[realname] = ctx.response
        elif isinstance(realtype, type) and realtype != service_type \
                and issubclass(realtype, Service):
            params[realname] = fetch_service(ctx, realtype)
        else:
            raise KeyError('%s.__init__(%s) param type is empty or wrong!' % (str(service_type), realname))
    return service_type(**params)


def fetch_model(ctx: Context, model_type: Type[Model]):
    """
        >>> from lessweb.storage import Storage
        >>> class Person(Model):
        ...     name: str
        ...     age: int
        ...     weight: int
        >>> ctx = Context()
        >>> ctx.set_alias('weight', 'w')
        >>> ctx._fields = dict(name='Bob', age='33', w='100', x='1')
        >>> model = fetch_model(ctx, Person)
        >>> assert Storage.of(model) == {'name': 'Bob', 'age': 33, 'weight': 100}, model.items()
    """
    object = model_type()
    bridge = BaseBridge()
    bridge.init_for_cast(ctx.app.bridges)
    fields = ctx.get_inputs()
    for realname, realtype in get_type_hints(model_type).items():
        if realname[0] == '_': continue  # 私有成员不赋值
        queryname = ctx._aliases.get(realname, realname)
        if queryname not in fields:  # 缺输入
            if generic_origin(realtype) == Optional:
                setattr(object, realname, None)
            else:
                pass  # 不赋值&不报错
        elif realtype == UploadedFile:
            queryvalue = fields[queryname]
            if not isinstance(queryvalue, UploadedFile):
                raise BadParamError(query=realname, error='Uploaded File Only')
            setattr(object, realname, queryvalue)
        else:  # 输入的类型转换
            try:
                queryvalue = fields[queryname]
                realvalue = bridge.cast(queryvalue, type(queryvalue), realtype)
                setattr(object, realname, realvalue)
            except (ValueError, TypeError) as e:
                raise BadParamError(query=realname, error=str(e))
    return object


def fetch_param(ctx: Context, fn: Callable):
    """
        >>> def get_person(ctx:Context, name:str, age:int, weight:int, createAt:int=2):
        ...     pass
        >>> ctx = Context()
        >>> ctx.set_alias('weight', 'w')
        >>> ctx._fields = dict(name='Bob', age='33', w='100', weight='1', createAt='9')
        >>> param = fetch_param(ctx, get_person)
        >>> assert param == {'ctx': ctx, 'name': 'Bob', 'age': 33, 'weight': 100, 'createAt': 2}, param
    """
    result = {}
    bridge = BaseBridge()
    bridge.init_for_cast(ctx.app.bridges)
    fields = ctx.get_inputs()
    for realname, (realtype, has_default) in func_arg_spec(fn).items():
        if realname == 'return': continue
        if realtype == Context:
            result[realname] = ctx
        elif realtype == Request:
            result[realname] = ctx.request
        elif realtype == Response:
            result[realname] = ctx.response
        elif isinstance(realtype, type) and issubclass(realtype, Service):
            result[realname] = fetch_service(ctx, realtype)
        elif isinstance(realtype, type) and issubclass(realtype, Model):
            result[realname] = fetch_model(ctx, realtype)
        else:
            queryname = ctx._aliases.get(realname, realname)
            if queryname not in fields:  # 缺输入
                if has_default:
                    pass  # 不赋值&不报错
                elif generic_origin(realtype) == Optional:
                    result[realname] = None
                else:
                    raise NeedParamError(query=realname, doc='Missing Required Param')
            elif realtype == UploadedFile:
                queryvalue = fields[queryname]
                if not isinstance(queryvalue, UploadedFile):
                    raise BadParamError(query=realname, error='Uploaded File Only')
                result[realname] = queryvalue
            else:  # 输入的类型转换
                try:
                    queryvalue = fields[queryname]
                    result[realname] = bridge.cast(queryvalue, type(queryvalue), realtype)
                except (ValueError, TypeError) as e:
                    raise BadParamError(query=realname, error=str(e))
    return result


class ModelToDict(Bridge):
    def __init__(self, source: Model):
        self.value = source

    def to(self) -> Jsonizable:
        ret = {}
        for name, type_ in get_type_hints(type(self.value)).items():
            if hasattr(self.value, name) and name[0] != '_':
                value = self.cast(getattr(self.value, name), type_, Jsonizable)
                ret[name] = value
        return ret
