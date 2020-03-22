from typing import Callable, Optional, Type, get_type_hints, TypeVar, Generic, Dict, Any
from abc import ABCMeta

from .context import Context, Request, Response
from .webapi import NeedParamError, BadParamError
from .bridge import Jsonizable, MultipartFile
from .typehint import optional_core, generic_core, is_optional_type, is_generic_type, get_origin
from .utils import func_arg_spec
from .storage import Storage
from .bridge import RequestBridge


__all__ = ["Model", "Service"]


T = TypeVar('T')


class Model(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value: T = value

    def __call__(self) -> T:
        return self.value

    def __str__(self):
        return f'lessweb.Model[{type(self.value)}]'


class Service(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value: T = value

    def __call__(self) -> T:
        return self.value

    def __str__(self):
        return f'lessweb.Model[{type(self.value)}]'


def fetch_service(ctx: Context, service_type: Type):
    """
    :return:  Service[service_type]
    """
    params: Dict[str, Any] = {}
    for realname, realtype in get_type_hints(service_type).items():
        if realtype == Context:
            params[realname] = ctx
        elif realtype == Request:
            params[realname] = ctx.request
        elif realtype == Response:
            params[realname] = ctx.response
        elif is_generic_type(realtype) and get_origin(realtype) == Service:
            params[realname] = fetch_service(ctx, generic_core(realtype))
        else:
            pass  # 其他类型不注入
    if issubclass(service_type, Service): raise LookupError(service_type)
    obj = service_type()
    for key, val in params.items():
        setattr(obj, key, val)
    return Service(obj)


def fetch_model(ctx: Context, bridge: RequestBridge, core_type: Type, origin_type: Type):
    """
    :return:  origin_type[core_type]
    """
    fields: Dict[str, Any] = {}
    for realname, realtype in get_type_hints(core_type).items():
        if realname[0] == '_': continue  # 私有成员不赋值
        queryname = ctx.request._aliases.get(realname, realname)
        inputval = ctx.request.get_input(queryname)
        if is_optional_type(realtype):
            realtype = optional_core(realtype)
        if not isinstance(realtype, type):
            continue
        if inputval is not None:
            try:
                fields[realname] = bridge.cast(inputval, realtype)
            except (ValueError, TypeError) as e:
                raise BadParamError(query=realname, error=str(e))
        else:
            pass  # 不赋值&不报错
    if origin_type == Model:
        if issubclass(core_type, Model): raise LookupError(core_type)
        obj = core_type()
        for key, val in fields.items():
            setattr(obj, key, val)
        return Model(obj)


def fetch_param(ctx: Context, fn: Callable) -> Dict[str, Any]:
    """
    fn: dealer function
    return: Dict[realname, Context|Request|Response|Model|...]
    """
    result: Dict[str, Any] = {}
    bridge = RequestBridge(ctx.app.request_bridges)
    for realname, (realtype, has_default) in func_arg_spec(fn).items():
        if realname == 'return': continue
        if realtype == Context:
            result[realname] = ctx
        elif realtype == Request:
            result[realname] = ctx.request
        elif realtype == Response:
            result[realname] = ctx.response
        elif is_generic_type(realtype):
            if get_origin(realtype) == Service:
                result[realname] = fetch_service(ctx, generic_core(realtype))
            elif get_origin(realtype) == Model:
                result[realname] = fetch_model(ctx, bridge, generic_core(realtype), Model)
        else:
            if is_optional_type(realtype):
                realtype = optional_core(realtype)
            if not isinstance(realtype, type):
                continue
            queryname = ctx.request._aliases.get(realname, realname)
            inputval = ctx.request.get_input(queryname)
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
