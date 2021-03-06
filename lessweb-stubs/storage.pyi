from typing import TypeVar, Type
__all__ = ["Storage"]

T = TypeVar('T')


class Storage(dict):
    def __getattr__(self, key): ...
    def __setattr__(self, key, value): ...
    def __delattr__(self, key): ...
    def __repr__(self): ...
    def __sub__(self, other): ...
    @staticmethod
    def type_hints(cls: Type) -> 'Storage': ...
    @staticmethod
    def of(obj) -> 'Storage': ...
    def to(self, cls: Type[T]) -> T: ...
