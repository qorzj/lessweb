from typing import Callable, Type, TypeVar, Generic, Dict, Any
from abc import ABCMeta

from lessweb.context import Context
from lessweb.bridge import RequestBridge


__all__ = ["Model", "Service"]


T = TypeVar('T')


class Model(Generic[T]):
    value: T
    def __init__(self, value: T) -> None: ...
    def get(self) -> T: ...
    def __str__(self) -> str: ...


class Service(metaclass=ABCMeta): ...
def fetch_service(ctx: Context, service_type: Type) -> Any: ...
def fetch_model(ctx: Context, bridge: RequestBridge, core_type: Type, origin_type: Type) -> Any: ...
def fetch_param(ctx: Context, fn: Callable) -> Dict[str, Any]: ...
