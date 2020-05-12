from typing import Callable, Optional, Type, get_type_hints, Dict, Any, List, Tuple

from functools import lru_cache
from .context import Context, Request, Response
from .webapi import BadParamError
from .bridge import ParamStr
from .typehint import optional_core, generic_core, is_generic_type, get_origin
from .utils import func_arg_spec
from .storage import Storage


__all__ = ['request_bridge']


@lru_cache(maxsize=None)
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
    target_is_optional, target_type = optional_core(target_type)
    if inputval is None:
        if target_is_optional:
            return None
        else:
            raise ValueError("Cannot assign None when expected %s" % target_type)
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
    elif isinstance(inputval, target_type):
        return inputval
    else:
        return target_type(inputval)


def fetch_model(ctx: Context, target_type: Type) -> Any:
    if is_generic_type(target_type) and get_origin(target_type) == list:
        if not ctx.request.is_json():
            raise ValueError("Need JSON request when expected %s" % target_type)
        inputval = ctx.request.json_input
        if not isinstance(inputval, list):
            raise ValueError("Need JSON array request when expected %s" % target_type)
        item_type = generic_core(target_type)
        return [request_bridge(item, item_type) for item in inputval]
    else:
        target_obj = target_type()
        for realname, prop_type in Storage.type_hints(target_type).items():
            queryname = ctx.request._aliases.get(realname, realname)
            inputval = ctx.request.get_input(queryname)
            if inputval is not None:
                try:
                    setattr(target_obj, realname, request_bridge(inputval, prop_type))
                except Exception as e:
                    raise BadParamError(param=realname, message=str(e))
            else:
                pass  # 不赋值&不报错
        return target_obj


def fetch_param(ctx: Context, fn: Callable) -> Tuple[List, Dict[str, Any]]:
    """
    fn: dealer function
    return: Dict[realname, Context|Request|Response|Model|...]
    """
    args: List = []
    kwargs: Dict[str, Any] = {}
    for realname, (realtype, has_default, positional_only) in func_arg_spec(fn).items():
        value: Any
        if realtype == Context:
            value = ctx
        elif realtype == Request:
            value = ctx.request
        elif realtype == Response:
            value = ctx.response
        elif model_or_service(realtype) == 2:
            value = fetch_service(ctx, realtype)
        else:
            _, realtype = optional_core(realtype)
            if not isinstance(realtype, type) and not is_generic_type(realtype):
                raise BadParamError(param=realname, message='Unsupported type %s' % realtype)
            if positional_only:
                value = fetch_model(ctx, realtype)
            else:
                queryname = ctx.request._aliases.get(realname, realname)
                inputval = ctx.request.get_input(queryname)
                if inputval is not None:
                    try:
                        value = request_bridge(inputval, realtype)
                    except Exception as e:
                        raise BadParamError(param=realname, message=str(e))
                elif not has_default:
                    raise BadParamError(param=realname, message='Missing required param')
                else:
                    continue  # 不赋值&不报错
        # 将value追加到args或kwargs
        if positional_only:
            args.append(value)
        else:
            kwargs[realname] = value

    return args, kwargs
