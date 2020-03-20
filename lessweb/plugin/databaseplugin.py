from typing import Type, TypeVar, get_type_hints, Iterable, List, Iterator
from enum import Enum
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import as_declarative, declared_attr

from ..context import Context
from ..application import Application


__all__ = ["DatabasePlugin", "DbModel", "DbServ", "cast_model"]


class DatabaseKey(Enum):
    session = 1


class DatabasePlugin:
    def __init__(self, uri, echo=True, autoflush=True, autocommit=False, patterns=('.*',), createtables=()):
        self.patterns = patterns
        if '://' not in uri:
            uri = 'sqlite:///' + uri
        engine = create_engine(uri, pool_recycle=3600)
        engine.echo = echo
        self.db_session_maker = scoped_session(sessionmaker(
                autoflush=autoflush, autocommit=autocommit, bind=engine))
        self.db_engine = engine
        self.autocommit = autocommit
        for table in createtables:
            table.metadata.create_all(self.db_engine)

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


@as_declarative()
class DbModel(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__

    def __repr__(self):
        return '<DbModel ' + repr(list(self.__dict__.items())) + '>'


class DbServ:
    ctx: Context

    @property
    def db(self) -> Session:
        session = self.ctx.box.get(DatabaseKey.session)
        if session is None:
            raise ValueError('database session not available')
        return session


T = TypeVar('T')
U = TypeVar('U')


def cast_model(model_class: Type[T], query_result) -> T:
    model_object = model_class()
    model_keys = get_type_hints(model_class)
    if query_result is None:
        return model_object

    if hasattr(query_result, '__table__'):  # 单个对象
        for key in query_result.__table__.columns.keys():
            if key in model_keys:
                setattr(model_object, key, getattr(query_result, key))
        return model_object
    elif hasattr(query_result, 'keys'):  # sqlalchemy.util._collections.result
        for row_key in query_result.keys():
            row_val = getattr(query_result, row_key)
            if hasattr(row_val, '__table__'):  # DbModel
                for key in row_val.__table__.columns.keys():
                    if key in model_keys:
                        setattr(model_object, key, getattr(row_val, key))
            else:  # 普通对象
                setattr(model_object, row_key, row_val)

        return model_object
    else:
        raise TypeError('Cannot cast %s to Model' % str(query_result))
