from typing import Callable, Optional, Type, get_type_hints, Dict, Any, List

from functools import lru_cache
from .context import Context, Request, Response
from .webapi import BadParamError
from .bridge import ParamStr
from .typehint import optional_core, generic_core, is_optional_type, is_generic_type, get_origin
from .utils import func_arg_spec
from .storage import Storage


__all__ = ['request_bridge']


@lru_cache
def model_or_service(cls: Type) -> int:
    """
    :return: 1=Model 2=Service 0=None
    """
    try:
        for prop_type in get_type_hints(cls).values():
            if prop_type == int or prop_type == str:
                return 1
            elif prop_type == Context or prop_type == Request or prop_type == Response \
                    or model_or_service(prop_type) == 2:
                return 2
            else:
                return 1
        return 0
    except:
        return 0


def fetch_service(ctx: Context, service_type: Type):
    """
    :return:  cast(service_type, ctx)
    """
    params: Dict[str, Any] = {}
    for realname, realtype in Storage.type_hints(service_type).items():
        if realtype == Context:
            params[realname] = ctx
        elif realtype == Request:
            params[realname] = ctx.request
        elif realtype == Response:
            params[realname] = ctx.response
        elif model_or_service(realtype) == 2:
            params[realname] = fetch_service(ctx, realtype)
        else:
            pass  # 其他类型不注入
    service_obj = service_type()
    for key, val in params.items():
        setattr(service_obj, key, val)
    return service_obj


def request_bridge(inputval: Any, target_type: Type):
    """
    :return:  cast(target_type, inputval)
    """
    if target_type == Any:
        return inputval
    if inputval is None:
        if is_optional_type(target_type):
            return None
        else:
            raise ValueError("Cannot assign None when expected %s" % target_type)
    if is_optional_type(target_type):
        target_type = optional_core(target_type)
    if isinstance(inputval, ParamStr):
        if issubclass(target_type, int):
            return target_type(int(inputval))
        else:
            return target_type(inputval)
    if isinstance(inputval, dict):
        if model_or_service(target_type) == 1:
            target_obj = target_type()
            for prop_name, prop_type in Storage.type_hints(target_type).items():
                if prop_name in inputval:
                    prop_value = request_bridge(inputval[prop_name], prop_type)
                    setattr(target_obj, prop_name, prop_value)
            return target_obj
        else:
            return target_type(**inputval)
    elif isinstance(inputval, list):
        if is_generic_type(target_type) and get_origin(target_type) == list:
            item_type = generic_core(target_type)
            return [request_bridge(item, item_type) for item in inputval]
        else:
            return target_type(*inputval)
    elif type(inputval) == target_type:
        return inputval
    else:
        return target_type(inputval)


def fetch_param(ctx: Context, fn: Callable) -> Dict[str, Any]:
    """
    fn: dealer function
    return: Dict[realname, Context|Request|Response|Model|...]
    """
    result: Dict[str, Any] = {}
    for realname, (realtype, has_default) in func_arg_spec(fn).items():
        if realname == 'return': continue
        if realtype == Context:
            result[realname] = ctx
        elif realtype == Request:
            result[realname] = ctx.request
        elif realtype == Response:
            result[realname] = ctx.response
        elif model_or_service(realtype) == 2:
            result[realname] = fetch_service(ctx, realtype)
        else:
            if is_optional_type(realtype):
                realtype = optional_core(realtype)
            if not isinstance(realtype, type):
                continue
            queryname = ctx.request._aliases.get(realname, realname)
            inputval = ctx.request.get_input(queryname)
            if inputval is not None:
                try:
                    result[realname] = request_bridge(inputval, realtype)
                except Exception as e:
                    raise BadParamError(param=realname, message=str(e))
            elif not has_default:
                raise BadParamError(param=realname, message='Missing required param')
            else:
                pass  # 不赋值&不报错

    return result
