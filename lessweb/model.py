from typing import Callable, Optional, Type, get_type_hints, TypeVar, Generic
from abc import ABCMeta

from .context import Context, Request, Response
from .webapi import NeedParamError, BadParamError
from .bridge import Jsonizable, MultipartFile
from .typehint import optional_core, generic_core, is_optional_type, is_generic_type, get_origin
from .utils import func_arg_spec
from .storage import Storage
from .bridge import RequestBridge


T = TypeVar('T')


class Model(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value: T = value

    def get(self) -> T:
        return self.value

    def __str__(self):
        return f'lessweb.Model[{type(self.value)}]'


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


def fetch_model(ctx: Context, bridge: RequestBridge, core_type: Type, origin_type: Type):
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
    fields = {}
    for realname, realtype in get_type_hints(core_type).items():
        if realname[0] == '_': continue  # 私有成员不赋值
        queryname = ctx.request._aliases.get(realname, realname)
        inputval = ctx.request.get_input(queryname)
        if not isinstance(realtype, type):
            continue
        if is_optional_type(realtype):
            realtype = optional_core(realtype)
        if inputval is not None:
            try:
                fields[realname] = bridge.cast(inputval, realtype)
            except (ValueError, TypeError) as e:
                raise BadParamError(query=realname, error=str(e))
        else:
            pass  # 不赋值&不报错
    if origin_type == Model:
        object = core_type()
        for key, val in fields.items():
            setattr(object, key, val)
        return Model(object)


def fetch_param(ctx: Context, fn: Callable):
    """
        >>> def get_person(ctx:Context, name:str, age:int, weight:int, createAt:int=2):
        ...     pass
        >>> ctx = Context()
        >>> ctx.request.set_alias('weight', 'w')
        >>> ctx._fields = dict(name='Bob', age='33', w='100', weight='1', createAt='9')
        >>> param = fetch_param(ctx, get_person)
        >>> assert param == {'ctx': ctx, 'name': 'Bob', 'age': 33, 'weight': 100, 'createAt': 2}, param
    """
    result = {}
    bridge = RequestBridge(ctx.app.request_bridges)
    for realname, (realtype, has_default) in func_arg_spec(fn).items():
        if realname == 'return': continue
        if not isinstance(realtype, type): continue
        if realtype == Context:
            result[realname] = ctx
        elif realtype == Request:
            result[realname] = ctx.request
        elif realtype == Response:
            result[realname] = ctx.response
        elif issubclass(realtype, Service):
            result[realname] = fetch_service(ctx, realtype)
        elif is_generic_type(realtype):
            if get_origin(realtype) == Model:
                result[realname] = fetch_model(ctx, bridge, generic_core(realtype), Model)
        else:
            queryname = ctx.request._aliases.get(realname, realname)
            inputval = ctx.request.get_input(queryname)
            realtype = optional_core(realtype)
            if is_optional_type(realtype):
                realtype = optional_core(realtype)
            if inputval is not None:
                try:
                    result[realname] = bridge.cast(inputval, realtype)
                except (ValueError, TypeError) as e:
                    raise BadParamError(query=realname, error=str(e))
            elif not has_default:
                raise NeedParamError(query=realname, doc='Missing Required Param')
            else:
                pass  # 不赋值&不报错

    return result
