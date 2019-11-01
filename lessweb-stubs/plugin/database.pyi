from typing import Any, overload, Type, TypeVar, get_type_hints, Iterable, List
from urllib.parse import quote
from enum import Enum

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import as_declarative, declared_attr

from ..context import Context
from ..model import Service

__all__ = ["global_data", "DbModel", "DbServ", "init", "processor", "create_all", "make_session",
           "cast_model", "cast_models"]


class DatabaseKey(Enum):
    session: int = ...


class GlobalData:
    db_session_maker: Any
    db_engine: Any
    autocommit: bool


class DbServ(Service):
    ctx: Context
    db: Session
    def __init__(self, ctx: Context) -> None: ...


global_data: GlobalData = ...


@as_declarative()
class DbModel(object):
    @declared_attr
    def __tablename__(cls) -> str: ...
    def __repr__(self): ...


@overload
def init(*, dburi, echo=True, autoflush=True, autocommit=False): ...
@overload
def init(*, protocol, username, password, host, port:int, database, echo=True, autoflush=True, autocommit=False): ...
def init(*, protocol=None, username=None, password=None, host=None, port:int=None, database=None, dburi=None,
         echo:bool=True, autoflush=True, autocommit=False) -> None: ...


def processor(ctx: Context): ...
def create_all(*DbModelClass) -> None: ...


class make_session:
    session: Session
    def __init__(self) -> None: ...
    def __enter__(self) -> Session: ...
    def __exit__(self, type_, value, traceback): ...


T = TypeVar('T')
U = TypeVar('U')


def cast_model(modelCls: Type[T], tblObjs) -> T: ...
def cast_models(modelCls: Type[T], tblObjsList) -> List[T]: ...
