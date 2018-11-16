from draft.model import *
import inspect
from draft.util.typehint import generic_origin, list_core, tuple_core


class InspectSpecItem(NamedTuple):  # /*函数参数属性*/
    optional: bool
    typehint: Any

    @staticmethod
    def inspect(f: Callable) -> Dict[str, 'InspectSpecItem']:
        ret = {}
        argspec = inspect.getfullargspec(f)
        args_size = len(argspec.args)
        defaults_size = len(argspec.defaults)
        for i, name in enumerate(argspec.args):
            optional = (args_size - i <= defaults_size)
            typehint = argspec.annotations.get(name, Any)
            ret[name] = InspectSpecItem(optional=optional, typehint=typehint)

        for name in argspec.kwonlyargs:
            optional = (name in argspec.kwonlydefaults)
            typehint = argspec.annotations.get(name, Any)
            ret[name] = InspectSpecItem(optional=optional, typehint=typehint)

        return ret


def realnames_of(ctx: Context) -> List[str]:
    return [ctx.realname_of(queryname) for queryname in ctx.get_inputnames()]


def input_value_of(ctx: Context, realname: str):
    queryname = ctx.queryname_of(realname)
    return ctx.get_input(queryname)


def realvalue_of(ctx: Context, input_value: Union[Jsonizable, UploadedFile], target: Type):
    if target == Context:
        return ctx
    elif target == Response:
        return ctx.response
    elif target == Request:
        return ctx.request
    elif issubclass(target, (Model, Service)):
        return inject_class(ctx, target)
    elif isinstance(input_value, UploadedFile):
        if target != UploadedFile:
            raise BadParamError
        return input_value
    elif target == List or generic_origin(target) == list:
        return [realvalue_of(ctx, x, list_core(target)) for x in input_value]
    elif target == Tuple or generic_origin(target) == tuple:
        return tuple(realvalue_of(ctx, x, tuple_core(target)) for x in input_value)
    elif target == Any:
        return input_value
    else:
        func = ctx.get_cast(Jsonizable, target)
        assert func is not None
        return func(input_value)


def inject_function(ctx: Context, dealer: Callable) -> Any:
    """
    根据函数定义和上下文，注入函数的参数并获得函数的调用结果。
    不用get_type_hints()是因为会从f(a:int=None)解析出a:Optional[int]
    """
    params = {}
    realnames = realnames_of(ctx)
    for realname, (optional, typehint) in InspectSpecItem.inspect(dealer):
        if realname in realnames:
            # realvalue = cast(Any, [ctx, realname, typehint])
            input_value = input_value_of(ctx, realname)
            params[realname] = realvalue_of(ctx, input_value, typehint)
        elif not optional:
            raise NeedParamError
    return dealer(**params)


def inject_class(ctx: Context, cls: Type) -> Any:
    """
    根据类型cls和上下文，获得cls的示例。注意cls必须是Model的子类。
    """
    params = {}
    realnames = realnames_of(ctx)
    typehints = get_type_hints(cls)
    for realname, typehint in typehints.items():
        if realname in realnames:
            # realvalue = cast(Any, [ctx, realname, typehint])
            input_value = input_value_of(ctx, realname)
            params[realname] = realvalue_of(ctx, input_value, typehint)

    obj = cls(**params)
    for realname in typehints:
        if not hasattr(obj, realname):
            raise NeedParamError

    return obj


def jsonizable_of(ctx: Context, data) -> Jsonizable:
    cls = type(data)
    if cls == list or cls == tuple:
        return [jsonizable_of(ctx, item) for item in data]
    elif issubclass(cls, Model):
        return {k: jsonizable_of(ctx, getattr(data, k)) for k in get_type_hints(cls)}
    else:
        func = ctx.get_cast(cls, Jsonizable)
        if func is not None:
            return func(data)
        else:
            return data


