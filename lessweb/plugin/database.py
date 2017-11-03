import time

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import InterfaceError
from sqlalchemy.ext.declarative import declarative_base

from ..storage import global_data
from ..model import Model

__all__ = ["DbModel", "init", "processor", "create_all", "make_session"]


def _db_model_items(self):
    return {k: v for k, v in self.__dict__.items() if k[0] != '_'}


def _db_model_setall(self, **kwargs):
    for k, v in kwargs.items():
        if k[0] != '_':
            setattr(self, k, v)


def _db_model_copy(self, **kwargs):
    ret = self.__class__()
    ret.setall(**self.items())
    ret.setall(**kwargs)
    return ret


DbModel: Model = declarative_base()
DbModel.items = _db_model_items
DbModel.setall = _db_model_setall
DbModel.copy = _db_model_copy
DbModel.__eq__ = lambda self, other: self is other or (type(self) == type(other) and self.items() == other.items())
DbModel.__repr__ = lambda self: '<DbModel ' + repr(self.items()) + '>'


def init(conf):
    if 'dburi' in conf:
        engine = create_engine(conf['dburi'])
    else:
        engine = create_engine(
            '{protocol}://{username}:{password}@{host}:{port}/{entity}'.format(**conf),
            pool_recycle=3600
        )
    engine.echo = conf.get('echo', conf['echo'])
    global_data.db_session_maker = sessionmaker(bind=engine)
    global_data.db_engine = engine


def processor(ctx):
    try:
        ctx.db = global_data.db_session_maker()
        ctx.will_commit = False
        ret = ctx()
        if ctx.will_commit:
            ctx.db.commit()
    except:
        ctx.db.rollback()
        raise
    finally:
        ctx.db.close()
    return ret


def create_all(timeout=0):
    start_at = time.time()
    while 1:
        try:
            DbModel.metadata.create_all(global_data.db_engine)
            return
        except InterfaceError as e:
            if time.time() - start_at > timeout:
                raise e
            time.sleep(1)


@contextmanager
def make_session():
    session = None
    try:
        session = global_data.db_session_maker()
        yield session
    except:
        session.rollback()
        raise
    finally:
        session.close()
