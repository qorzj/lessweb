from typing import Type, TypeVar, Iterable, Iterator, Any
from enum import Enum
from contextlib import contextmanager

from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import as_declarative, declared_attr

from lessweb.context import Context
from lessweb.application import Application


__all__ = ["DatabasePlugin", "DbModel", "DbServ", "cast_model"]


class DatabaseKey(Enum):
    session: int = ...


class DatabasePlugin:
    def __init__(self, uri: str, echo: bool=..., autoflush: bool=..., autocommit: bool=...,
                 patterns: Iterable[str]=..., createtables: Iterable[str]=...) -> None: ...
    def processor(self, ctx: Context) -> Any: ...
    def init_app(self, app: Application) -> None: ...
    def teardown(self, exception: Exception) -> None: ...
    @contextmanager
    def make_session(self) -> Iterator[Session]: ...


@as_declarative()
class DbModel(object):
    @declared_attr
    def __tablename__(cls) -> str: ...
    def __repr__(self) -> str: ...


class DbServ:
    ctx: Context
    @property
    def db(self) -> Session: ...


T = TypeVar('T')


def cast_model(model_class: Type[T], query_result: Any) -> T: ...
