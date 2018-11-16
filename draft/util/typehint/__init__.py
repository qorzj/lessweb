from typing import *


def generic_origin(t):
    """
    Generic's origin type
    >>> generic_origin(List[int]) == list
    True
    >>> generic_origin(Tuple[str]) == tuple
    True
    >>> generic_origin(Union[str, int, None]) == Union
    True
    """
    return getattr(t, '__origin__', None)


def generic_args(t):
    """
    Generic's arg-types
    >>> generic_args(List[str])
    (<class 'str'>,)
    >>> generic_args(Union[str, int, None])
    (<class 'str'>, <class 'int'>, <class 'NoneType'>)
    >>> generic_args(Union[int, str, None])
    (<class 'int'>, <class 'str'>, <class 'NoneType'>)
    """
    return getattr(t, '__args__')


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
    return type(None)


def list_core(t):
    """
    t is List? Any : t is List[u]? u : NoneType
    >>> list_core(List)
    typing.Any
    >>> list_core(List[int])
    <class 'int'>
    >>> list_core(str)
    <class 'NoneType'>
    """
    if t == List:
        return Any
    if generic_origin(t) == list:
        args = generic_args(t)
        return args[0]
    return type(None)


def tuple_core(t):
    """
    t is Tuple? Any : t is Tuple[u]? u : NoneType
    >>> tuple_core(Tuple)
    typing.Any
    >>> tuple_core(Tuple[int])
    <class 'int'>
    >>> tuple_core(str)
    <class 'NoneType'>
    """
    if t == Tuple:
        return Any
    if generic_origin(t) == tuple:
        args = generic_args(t)
        return args[0]
    return type(None)