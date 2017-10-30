from contextlib import contextmanager
from typing import TypeVar, Generic


__all__ = ['_catch', '_eafp', '_nil', '_if', '_as', '_ext', '_is']

T = TypeVar('T')


@contextmanager
def _catch(default=None, exception=Exception):
    """
    `with catch(0) as x: x = int('a')` is equivalent to `x = int('a') ?? 0`
    """
    try:
        yield default
    except exception:
        pass


def _eafp(ask, default):
    """
    Easier to ask for forgiveness than permission
    `x = _eafp(lambda: int('a'), 0)` is equivalent to `x = int('a') ?? 0`
    """
    try:
        return ask()
    except:
        return default


class SugarNil:
    def __bool__(self):
        return False


_nil = SugarNil()


class _if:
    def __init__(self, is_true):
        self.is_true = is_true
        self.value = _nil

    def __rmatmul__(self, left_opnd):
        if self.value is _nil:
            self.value = left_opnd
            return self
        else:
            return self.value if self.is_true else left_opnd

    __ror__ = __rmatmul__
    __call__ = __rmatmul__


class _as(Generic[T]):
    def __init__(self, cls: T):
        self.cls = cls

    def __enter__(self)->T:
        return self.cls

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class _ext:
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __rmatmul__(self, other):
        return self.fn(other, *self.args, **self.kwargs)

    __ror__ = __rmatmul__


class _is:
    def __init__(self, cls):
        self.cls = cls

    def __rmatmul__(self, other)->bool:
        return isinstance(other, self.cls) or (
            issubclass(self.cls, tuple) and hasattr(self.cls, '_fields') and
            all(hasattr(other, k) for k in self.cls._fields)
        )

    __ror__ = __rmatmul__
    __call__ = __rmatmul__
