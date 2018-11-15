"""
[hint, input, output, algorithm, sample]

"""
from typing import *


def true(_: Any) -> bool:
    pass


def false(_: Any) -> bool:
    pass


def nil(_: Any) -> bool:
    return _ is None


T = TypeVar('T')
U = TypeVar('U')


def eafp(onSuccess: T, onError: U) -> Union[T, U]:
    return onSuccess if onSuccess else onError


def At_(*a, **b):
    return True


ø: Dict
del T, U
