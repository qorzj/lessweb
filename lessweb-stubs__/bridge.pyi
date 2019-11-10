from typing import Type, TypeVar, Any, Tuple, List
from abc import abstractmethod, ABCMeta


T = TypeVar('T')


class Bridge(metaclass=ABCMeta):
    bridges: List[Type['Bridge']]
    dist: Type
    @abstractmethod
    def __init__(self, source) -> None: ...
    @abstractmethod
    def to(self)->Any: ...
    def init_for_cast(self, bridges, dist=None) -> None: ...
    @classmethod
    def inspect(cls)->Tuple[Type, Type]: ...
    def cast(self, object: Any, source_type: Type, dist: Type[T]) -> T: ...


def assert_valid_bridge(bridge) -> None: ...
