from typing import get_type_hints, TypeVar, Type


__all__ = ["Storage"]

T = TypeVar('T')


class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.

        >>> o = Storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'
    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'

    def __sub__(self, other):
        if isinstance(other, str):
            if other in self:
                del self[other]
        else:
            for key in other:
                self.__sub__(key)
        return self

    @staticmethod
    def type_hints(cls: Type) -> 'Storage':
        result = Storage()
        for prop_name, prop_type in get_type_hints(cls).items():
            if prop_name[0] != '_':
                result[prop_name] = prop_type
            else:
                pub_name = prop_name[1:]
                if isinstance(getattr(cls, pub_name, None), property):
                    result[pub_name] = prop_type
        return result

    @staticmethod
    def of(obj) -> 'Storage':
        result = Storage()
        for name in get_type_hints(obj).keys():
            if name[0] == '_':
                name = name[1:]
            if hasattr(obj, name):
                result[name] = getattr(obj, name)
        return result

    def to(self, cls: Type[T]) -> T:
        obj = cls()
        for key, val in self.items():
            setattr(obj, key, val)
        return obj
