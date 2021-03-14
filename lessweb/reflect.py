import inspect
from typing import Type, Dict, List, Union, Tuple, get_type_hints
from typing_inspect import get_args, is_optional_type, get_origin, is_typevar, is_generic_type, \
    get_generic_bases  # type: ignore

nullable_cache = {}
classifier_cache = {}
arguments_cache = {}


def cache_decorator(cache, tp):
    def func(f):
        def g():
            if tp in cache:
                return cache[tp]
            result = f()
            cache[tp] = result
            return result
        return g
    return func


class PropertyType:
    tp: Type
    typevars: Dict[str, 'PropertyType']

    def __init__(self, tp: Type, typevars: Dict[str, 'PropertyType'] = None) -> None:
        self.tp = tp
        self.typevars = typevars or {}

    def _pre_split(self):
        type_origin = get_origin(self.tp)
        type_args = [(self.typevars[str(t)] if is_typevar(t) else PropertyType(t, self.typevars)) for t in
                     get_args(self.tp)]
        return type_origin, type_args

    def nullable(self) -> bool:
        @cache_decorator(nullable_cache, self.tp)
        def solve():
            type_origin, type_args = self._pre_split()
            if type_origin is None:
                type_origin = self.tp
            if is_typevar(type_origin):
                return self.typevars[str(type_origin)].nullable()
            if type_origin == Union and type_args:
                if any(True for t in type_args if t.classifier() is type(None)):
                    return True
            if type_origin is type(None):
                return True
            return False
        return solve()

    def classifier(self) -> Type:
        @cache_decorator(classifier_cache, self.tp)
        def solve():
            type_origin, type_args = self._pre_split()
            if type_origin is None:
                type_origin = self.tp
            if is_typevar(type_origin):
                type_origin = self.typevars[str(type_origin)].classifier()
            if type_origin == Union and type_args:
                type_args = tuple(t for t in type_args if t.classifier() is not type(None))
                if len(type_args) == 1:
                    type_origin = type_args[0].classifier()
            return type_origin
        return solve()

    def arguments(self) -> Tuple['PropertyType']:
        @cache_decorator(arguments_cache, self.tp)
        def solve():
            type_origin, type_args = self._pre_split()
            if is_typevar(type_origin):
                type_args = self.typevars[str(type_origin)].arguments()
            elif type_origin == Union and type_args:
                type_args = tuple(t for t in type_args if t.classifier() is not type(None))
                if len(type_args) == 1:
                    type_args = type_args[0].arguments()
            return type_args
        return solve()

    def generic_map(self) -> Dict[str, 'PropertyType']:
        generic_map = {}
        if is_generic_type(self.tp):
            generic_base = get_origin(self.tp)
            for k, v in zip(get_args(get_generic_bases(generic_base)[0]), PropertyType(self.tp).arguments()):
                generic_map[str(k)] = v
        return generic_map

    def __str__(self) -> str:
        clfr = self.classifier()
        show = getattr(clfr, '__name__', '') or getattr(clfr, '_name', repr(clfr))
        if self.arguments():
            show += '<' + ', '.join(str(t) for t in self.arguments()) + '>'
        if self.nullable() and clfr is not type(None):
            show += '?'
        return show


def properties(cls: Type, generic_args: Tuple[PropertyType] = None) -> Dict[str, PropertyType]:
    result = {}
    if generic_args is None:
        generic_map = PropertyType(cls).generic_map()
    else:
        generic_map = {str(k): v for k, v in zip(get_args(get_generic_bases(cls)[0]), generic_args)}
    if is_generic_type(cls):
        cls = get_origin(cls)
    for prop_name, prop_type in get_type_hints(cls).items():
        prop_type_wrap = PropertyType(prop_type, generic_map)
        if prop_name[0] != '_':
            result[prop_name] = prop_type_wrap
    for prop_name, member in inspect.getmembers(cls):
        if isinstance(member, property):
            anno_dict = get_type_hints(member.fget)
            if 'return' in anno_dict:
                result[prop_name] = PropertyType(anno_dict['return'], generic_map)
    return result


from typing import Generic, TypeVar, Optional

T = TypeVar('T')
U = TypeVar('U')


class Page(Generic[T, U]):
    total: int

    @property
    def parent(self) -> Optional[U]:
        return None

    children: Optional[List[T]]


if __name__ == '__main__':
    import jsonschema
    data = {"result": 3}
    schema = {'type': 'object', 'properties': {'result': {'type': 'integer', 'enum': [3, 4, 5]}}}
    jsonschema.validate(instance=data, schema=schema,
                        format_checker=jsonschema.draft7_format_checker)
