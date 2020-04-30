from typing import Type, TypeVar, Iterable, List, Iterator, Generic, Optional, Union, Dict, Any
from enum import Enum
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.session import Session

from ..context import Context
from ..application import Application
from ..storage import Storage
from ..typehint import is_optional_type


__all__ = ["DbPlugin", "DbServ", "Mapper"]


class DatabaseKey(Enum):
    session = 1


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
                 patterns: Iterable[str]=('.*',)):
        self.patterns = patterns
        if '://' not in uri:
            uri = 'sqlite:///' + uri
        engine = create_engine(uri, pool_recycle=3600)
        engine.echo = echo
        self.db_session_maker = scoped_session(sessionmaker(
                autoflush=autoflush, autocommit=autocommit, bind=engine))
        self.db_engine = engine
        self.autocommit = autocommit

    def processor(self, ctx: Context):
        db = self.db_session_maker()
        try:
            ctx.box[DatabaseKey.session] = db
            if self.autocommit:
                with db.begin():
                    return ctx()
            else:
                return ctx()
        except:
            db.rollback()
            raise
        finally:
            db.close()

    def init_app(self, app: Application):
        for pattern in self.patterns:
            segs = pattern.split()
            if len(segs) == 1:
                app.add_interceptor(pattern, method='*', dealer=self.processor)
            elif len(segs) == 2:
                app.add_interceptor(segs[1], method=segs[0], dealer=self.processor)

    def teardown(self, exception: Exception):
        pass

    @contextmanager
    def make_session(self) -> Iterator[Session]:
        session: Session = self.db_session_maker()
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


T = TypeVar('T')


class DbServ:
    ctx: Context

    @property
    def db(self) -> Session:
        session = self.ctx.box.get(DatabaseKey.session)
        if session is None:
            raise ValueError('database session not available')
        return session

    def mapper(self, cls: Type[T]) -> 'Mapper[T]':
        return Mapper(self.db, cls)


def table(*, name: str):
    def g(cls):
        setattr(cls, '__tablename__', name)
        return cls
    return g


class Mapper(Generic[T]):
    session: Session
    model_type: Type[T]
    tablename: str
    model_schema: Storage
    primary_key: str
    where_sqls: List[str]
    where_data: Dict
    orderby_sql: str = ''

    def __init__(self, session: Session, cls: Type[T]) -> None:
        self.session = session
        self.model_type = cls
        self.tablename = getattr(cls, '__tablename__', '') or cls.__name__
        self.model_schema = Storage.type_hints(cls)
        if not self.model_schema:
            raise TypeError('%s schema is empty!' % cls)
        self.primary_key = next(iter(self.model_schema))
        self.where_sqls = []
        self.where_data = {}

    def _where_clause(self) -> str:
        return ' and '.join(f'({s})' for s in self.where_sqls)

    def _full_select_sql(self) -> str:
        where_clause = self._where_clause()
        titles = ','.join(f'`{key}`' for key in self.model_schema)
        if where_clause:
            sql = f'SELECT {titles} FROM `{self.tablename}` WHERE {where_clause}'
        else:
            sql = f'SELECT {titles} FROM `{self.tablename}`'
        if self.orderby_sql:
            sql += f' ORDER BY {self.orderby_sql}'
        return sql

    def bridge(self, row) -> T:
        obj = self.model_type()
        for key, val in row.items():
            if key in self.model_schema:
                prop_type = self.model_schema[key]
                if val is None and is_optional_type(prop_type):
                    setattr(obj, key, val)
                elif val is not None:
                    setattr(obj, key, prop_type(val))
        return obj

    def select_count(self) -> int:
        where_clause = self._where_clause()
        if where_clause:
            sql = f'SELECT COUNT(1) FROM `{self.tablename}` WHERE {where_clause}'
        else:
            sql = f'SELECT COUNT(1) FROM `{self.tablename}`'
        return self.session.execute(sql, self.where_data).scalar()

    def select_first(self) -> Optional[T]:
        sql = self._full_select_sql() + ' LIMIT 1'
        row = self.session.execute(sql, self.where_data).first()
        if row is None:
            return None
        return self.bridge(row)

    def select(self) -> List[T]:
        ret = []
        sql = self._full_select_sql()
        rows = self.session.execute(sql, self.where_data)
        for row in rows:
            ret.append(self.bridge(row))
        return ret

    def insert(self, obj: T, commit: bool=True) -> None:
        titles = ','.join(f'`{key}`' for key in self.model_schema)
        slots = ','.join(f':{key}' for key in self.model_schema)
        sql = f'INSERT INTO `{self.tablename}` ({titles}) VALUES ({slots})'
        result = self.session.execute(sql, Storage.of(obj))
        setattr(obj, self.primary_key, result.lastrowid)
        if commit:
            self.session.commit()

    def insert_if_not_exist(self, obj: T, commit: bool=True) -> None:
        obj_storage = Storage.of(obj)
        titles = ','.join(f'`{key}`' for key in obj_storage.keys())
        slots = ','.join(f':{key}_1' for key in obj_storage.keys())
        data = {f'{key}_1': val for key, val in obj_storage.items()}
        data.update(self.where_data)
        where_clause = self._where_clause()
        if not where_clause:
            raise ValueError(f'WHERE clause cannot be empty for INSERT_IF_NOT_EXIST!')
        sql = f'INSERT INTO `{self.tablename}` ({titles}) SELECT {slots}' + \
            f' WHERE not exists ( SELECT 1 FROM `{self.tablename}` WHERE {where_clause})'
        self.session.execute(sql, data)
        if commit:
            self.session.commit()

    def update(self, obj: T, commit: bool=True) -> None:
        obj_storage = Storage.of(obj)
        set_sql = ', '.join(f'`{key}`=:{key}_1' for key in obj_storage.keys())
        data = {f'{key}_1': val for key, val in obj_storage.items()}
        data.update(self.where_data)
        where_clause = self._where_clause()
        if not where_clause:
            raise ValueError(f'WHERE clause cannot be empty for UPDATE!')
        sql = f'UPDATE `{self.tablename}` SET {set_sql} WHERE {where_clause}'
        self.session.execute(sql, data)
        if commit:
            self.session.commit()

    def increment(self, obj: T, commit: bool=True) -> None:
        obj_dict = {key: val for key, val in Storage.of(obj).items() if isinstance(val, int)}
        set_sql = ', '.join(f'`{key}`=`{key}`+(:{key}_1)' for key in obj_dict.keys())
        data = {f'{key}_1': val for key, val in obj_dict.items()}
        data.update(self.where_data)
        where_clause = self._where_clause()
        if not where_clause:
            raise ValueError(f'WHERE clause cannot be empty for increment UPDATE!')
        sql = f'UPDATE `{self.tablename}` SET {set_sql} WHERE {where_clause}'
        self.session.execute(sql, data)
        if commit:
            self.session.commit()

    def delete(self, commit: bool=True) -> None:
        where_clause = self._where_clause()
        if not where_clause:
            raise ValueError(f'WHERE clause cannot be empty for DELETE!')
        sql = f'DELETE FROM `{self.tablename}` WHERE {where_clause}'
        self.session.execute(sql, self.where_data)
        if commit:
            self.session.commit()

    def by_id(self, primary_key: Union[int, str]) -> 'Mapper[T]':
        sql = f'`{self.primary_key}`=:{self.primary_key}'
        data = {self.primary_key: primary_key}
        self.where_sqls.append(sql)
        self.where_data.update(data)
        return self

    def and_equal(self, obj: T) -> 'Mapper[T]':
        data = Storage.of(obj)
        self.where_data.update(data)
        for key, val in data.items():
            sql = f'`{key}`=:{key}'
            self.where_sqls.append(sql)
        return self

    def and_(self, clause: str, obj: T) -> 'Mapper[T]':
        self.where_sqls.append(clause)
        self.where_data.update(Storage.of(obj))
        return self

    def order_desc(self) -> 'Mapper[T]':
        self.orderby_sql = f'`{self.primary_key}` desc'
        return self

    def order_by(self, clause: str) -> 'Mapper[T]':
        self.orderby_sql = clause
        return self
