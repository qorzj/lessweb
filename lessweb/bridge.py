from typing import Type, TypeVar, get_type_hints, Any, Tuple, List
from abc import abstractmethod, ABCMeta
from lessweb.typehint import issubtyping
from lessweb.utils import func_arg_spec


T = TypeVar('T')


class Bridge(metaclass=ABCMeta):
    bridges: List[Type['Bridge']]
    dist: Type

    @abstractmethod
    def __init__(self, source):
        pass

    @abstractmethod
    def to(self)->Any:
        pass

    def init_for_cast(self, bridges, dist=None):
        self.bridges = bridges
        self.dist = dist

    @classmethod
    def inspect(cls)->Tuple[Type, Type]:
        source_types = get_type_hints(cls.__init__)
        source_types.pop('return', None)
        source_type = source_types[list(source_types.keys())[-1]]
        dist_type = get_type_hints(cls.to)['return']
        return source_type, dist_type

    def cast(self, object: Any, source_type: Type, dist: Type[T]) -> T:
        if isinstance(object, (str, int, float)) and dist in (str, int, bool, float):
            return dist(object)
        for bridge in self.bridges:
            bridge_src, bridge_dist = bridge.inspect()
            if issubtyping(source_type, bridge_src) and issubtyping(bridge_dist, dist):
                b = bridge(object)
                b.init_for_cast(self.bridges, dist)
                return b.to()
        if issubtyping(source_type, dist):
            return object
        raise TypeError('Bridges cannot cast %s to %s' % (source_type, dist))


def assert_valid_bridge(bridge):
    assert issubclass(bridge, Bridge), f'{bridge} is not subclass of lessweb.Bridge'
    args = func_arg_spec(bridge.__init__)
    assert len(args) == 2, f'{bridge}.__init__ method must contain one parameter'
    arg_name = list(args.keys())[-1]
    source_types = get_type_hints(bridge.__init__)
    assert arg_name in source_types, f'{bridge}.__init__ parameter must contain type annotation'
    args = func_arg_spec(bridge.to)
    assert len(args) == 1, f'{bridge}.to method cannot contain parameter'
    dist_types = get_type_hints(bridge.to)
    assert 'return' in dist_types, f'{bridge}.to must contain type annotation of return'
