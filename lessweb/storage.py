from typing import get_type_hints
from unittest.mock import Mock


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
    def of(object):
        result = Storage()
        for name in get_type_hints(object).keys():
            result[name] = getattr(object, name)
        return result


class ChainMock:
    """
    Usage: https://github.com/qorzj/lessweb/wiki/%E7%94%A8mock%E6%B5%8B%E8%AF%95service
    """
    def __init__(self, path, return_value):
        self.returns = {}
        self.mock = {}
        self.join(path, return_value)

    def join(self, path, return_value):
        if not path.startswith('.'):
            path = '.' + path
        self.returns[path] = return_value
        self.mock[path] = Mock(return_value=return_value)
        while '.' in path:
            prefix, key = path.rsplit('.', 1)
            if prefix not in self.returns: self.returns[prefix] = Storage()
            self.returns[prefix][key] = self.mock[path]
            self.mock[prefix] = Mock(return_value=self.returns[prefix])
            path = prefix
        return self

    def __call__(self, path=None):
        if path is None:
            return self.mock['']()
        if not path.startswith('.'):
            path = '.' + path
        return self.mock[path]
