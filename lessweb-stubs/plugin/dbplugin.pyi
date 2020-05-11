from typing import Type, TypeVar, Iterable, List, Iterator, Generic, Optional, Union, Dict, Any
from enum import Enum
from contextlib import contextmanager

from sqlalchemy.orm.session import Session

from lessweb.context import Context
from lessweb.application import Application
from ..storage import Storage


__all__ = ["DbPlugin", "DbServ", "Mapper"]


class DatabaseKey(Enum):
    session: int = ...


class DbPlugin:
    patterns: Iterable[str]
    db_session_maker: Any
    db_engine: Any
    autocommit: bool
    def __init__(self,
                 uri: str,
                 echo: bool=True,
                 autoflush: bool=True,
                 autocommit: bool=False,
                 patterns: Iterable[str]=('.*',)): ...
    def processor(self, ctx: Context) -> Any: ...
    def init_app(self, app: Application) -> None: ...
    def teardown(self, exception: Exception) -> None: ...
    @contextmanager
    def make_session(self) -> Iterator[Session]: ...


T = TypeVar('T')


class DbServ:
    ctx: Context
    @property
    def db(self) -> Session: ...
    def mapper(self, cls: Type[T]) -> 'Mapper[T]': ...


def table(*, name: str) -> Any: ...
def transient(*props: str) -> Any: ...


class Mapper(Generic[T]):
    session: Session
    model_type: Type[T]
    tablename: str
    model_schema: Storage
    primary_key: str
    _where_sqls: List[str]
    _where_data: Dict
    _orderby_sql: str

    def __init__(self, session: Session, cls: Type[T]) -> None: ...
    def _where_clause(self) -> str: ...
    def _full_select_sql(self) -> str: ...
    def _imtransient_storage(self, obj: T) -> Storage: ...
    def bridge(self, row) -> T: ...
    def select_count(self) -> int: ...
    def select_first(self) -> Optional[T]: ...
    def select(self) -> List[T]: ...
    def insert(self, obj: T, commit: bool=True) -> None: ...
    def insert_if_not_exist(self, obj: T, commit: bool=True) -> None: ...
    def update(self, obj: T, commit: bool=True) -> None: ...
    def increment(self, obj: T, commit: bool=True) -> None: ...
    def delete(self, commit: bool=True) -> None: ...
    def by_id(self, primary_key: Union[int, str]) -> 'Mapper[T]': ...
    def and_equal(self, obj: Union[T, Dict[str, Any]]) -> 'Mapper[T]': ...
    def and_(self, clause: str, data: Storage) -> 'Mapper[T]': ...
    def order_desc(self) -> 'Mapper[T]': ...
    def order_by(self, clause: str) -> 'Mapper[T]': ...
