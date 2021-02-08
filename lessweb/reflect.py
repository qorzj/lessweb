from typing import Type, Dict, List, Union, Iterable, get_type_hints
from typing_inspect import get_args, is_optional_type, get_origin  # type: ignore


class PropertyType:
    source: Type  # source type

    optional: bool  # whether or not is optional

    classifier: Type  # class declaration level types (ignore type arguments)

    arguments: Iterable['PropertyType']  # type arguments

    def __init__(self, tp: Type) -> None:
        self.source = tp
        self.optional = tp is type(None) or is_optional_type(tp)
        type_args = get_args(tp)
        type_origin = get_origin(tp)
        if type_args:
            type_args = tuple(PropertyType(t) for t in type_args if not (self.optional and t is type(None)))
        if type_origin == Union and len(type_args) == 1:
            type_origin, type_args = type_args[0].classifier, type_args[0].arguments
        if type_origin is None:
            type_origin = tp
        self.classifier = type_origin
        self.arguments = type_args

    def __str__(self) -> str:
        clfr = self.classifier
        show = getattr(clfr, '__name__', '') or getattr(clfr, '_name', '')
        if self.arguments:
            show += '<' + ', '.join(str(t) for t in self.arguments) + '>'
        if self.optional and clfr is not type(None):
            show += '?'
        return show


def properties(cls: Type) -> Dict[str, PropertyType]:
    result = {}
    for prop_name, prop_type in get_type_hints(cls).items():
        prop_type_wrap = PropertyType(prop_type)
        if not prop_name.startswith('_'):
            result[prop_name] = prop_type_wrap
        else:
            public_name = prop_name.lstrip('_')
            if isinstance(getattr(cls, public_name, None), property):
                result[public_name] = prop_type_wrap
    return result


if __name__ == '__main__':
    print(PropertyType(Union[None, List[str]]))
    print(PropertyType(Dict[str, Union[int, float, bool, None]]))
    print(PropertyType(Union[None]))
