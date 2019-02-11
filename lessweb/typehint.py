from typing import *


NoneType = type(None)


class AnySub:
    def __init__(self, core: Type):
        self.__origin__ = AnySub
        self.__args__ = (core,)


def generic_origin(t):
    """
    Generic's origin type
    >>> generic_origin(List[int]) == List
    True
    >>> >>> generic_origin(list) == list
    True
    >>> generic_origin(Tuple[str]) == Tuple
    True
    >>> generic_origin(Union[str, int, None]) == Union
    True
    """
    return getattr(t, '__origin__', t) or t


def generic_args(t):
    """
    Generic's arg-types
    >>> generic_args(list) is None
    True
    >>> generic_args(Dict) is None
    True
    >>> generic_args(List[str])
    (<class 'str'>,)
    >>> generic_args(Union[str, int, None])
    (<class 'str'>, <class 'int'>, <class 'NoneType'>)
    >>> generic_args(Union[int, str, None])
    (<class 'int'>, <class 'str'>, <class 'NoneType'>)
    """
    if hasattr(t, '__origin__') and hasattr(t, '__args__'):
        return getattr(t, '__args__')
    else:
        return None


def optional_core(t):
    """
    t is Optaional? t.core : NoneType
    >>> optional_core(List[int])
    <class 'NoneType'>
    >>> optional_core(Optional[str])
    <class 'str'>
    >>> optional_core(Union[int, str])
    <class 'NoneType'>
    """
    if generic_origin(t) != Union:
        return type(None)
    args_with_none = generic_args(t)
    if len(args_with_none) != 2:
        return type(None)
    first, second = args_with_none
    if isinstance(None, first):
        return second
    elif isinstance(None, second):
        return first
    return NoneType


def collection_core(t: Type):
    """
    t is Collection? Any : t is Collection[u]? u : NoneType
    >>> collection_core(Tuple)
    typing.Any
    >>> collection_core(List[int])
    <class 'int'>
    >>> collection_core(str)
    <class 'NoneType'>
    """
    if not issubclass(t, Collection):
        return NoneType
    args = generic_args(t)
    return args[0] if args else None


def issubtyping(cls: Type, parent: Type):
    """
    >>> issubtyping(list, List[int])
    True
    >>> issubtyping(int, Union[int, str])
    True
    >>> issubtyping(Union[int, str], Union[int, float, str])
    True
    """
    # python3.7 List.__args__结果是(~T,), Dict.__args__结果是(~KT, ~VT)，而Tuple.__args__的结果是()
    # 因此要注意Tuple相当于Tuple[]（而直接写Tuple[]会报语法错误）
    if cls == Any or parent == Any or \
            isinstance(cls, TypeVar) or isinstance(parent, TypeVar):
        return True
    origin_cls = generic_origin(cls)
    origin_prt = generic_origin(parent)
    if origin_cls == Union:
        if origin_prt != Union:
            return all(issubtyping(arg_cls, parent) for arg_cls in generic_args(cls))
        return all(
            any(issubtyping(arg_cls, arg_prt) for arg_prt in generic_args(parent))
            for arg_cls in generic_args(cls)
        )
    elif origin_cls == AnySub:
        return issubtyping(parent, generic_args(cls)[0])
    else:
        if origin_prt == Union:
            return any(issubtyping(cls, arg_prt) for arg_prt in generic_args(parent))
        if issubclass(origin_cls, Collection) and issubclass(origin_prt, Collection):
            if not issubclass(origin_cls, origin_prt):
                return False
            args_cls = generic_args(cls)
            args_prt = generic_args(parent)
            if args_cls is None or args_prt is None:
                return True
            if len(args_cls) != len(args_prt):
                return False
            return all(issubtyping(arg_cls, arg_prt) for (arg_cls, arg_prt) in zip(args_cls, args_prt))
        return issubclass(origin_cls, origin_prt)
