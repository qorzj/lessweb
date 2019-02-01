from typing import Type, TypeVar, get_type_hints, Any, Tuple, Union, List, Dict, Optional
from abc import abstractmethod, ABCMeta
from lessweb.typehint import issubtyping


T = TypeVar('T')


class Bridge(metaclass=ABCMeta):
    bridges: List[Type['Bridge']]
    dist: Type

    def __init__(self, bridges, dist=None):
        self.bridges = bridges
        self.dist = dist

    @abstractmethod
    def of(self, source):
        pass

    @abstractmethod
    def to(self)->Any:
        pass

    @classmethod
    def inspect(cls)->Tuple[Type, Type]:
        source_type = get_type_hints(cls.of)['source']
        dist_type = get_type_hints(cls.to)['return']
        return source_type, dist_type

    def cast(self, object: Any, source_type: Type, dist: Type[T]) -> T:
        if isinstance(object, (str, int, float)) and dist in (str, int, bool, float):
            return dist(object)
        for bridge in self.bridges:
            bridge_src, bridge_dist = bridge.inspect()
            if issubtyping(source_type, bridge_src) and issubtyping(bridge_dist, dist):
                b = bridge(self.bridges, dist)
                b.of(object)
                return b.to()
        if issubtyping(source_type, dist):
            return object
        raise TypeError('Bridges cannot cast %s to %s' % (source_type, dist))
