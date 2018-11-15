from typing import *


def generic_origin(t):
    """
    Generic's origin type
    """
    return getattr(t, '__origin__', None)


def generic_args(t):
    """
    Generic's arg-types
    """
    return getattr(t, '__args__')


def optional_core(t):
    """
    t is Optaional? t.core : None
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
    if t == List:
        return Any
    if generic_origin(t) == List:
        args = generic_args(t)
        return args[0]
    return type(None)


def tuple_core(t):
    if t == Tuple:
        return Any
    if generic_origin(t) == Tuple:
        args = generic_args(t)
        return args[0]
    return type(None)