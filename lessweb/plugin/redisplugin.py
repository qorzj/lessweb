from typing import Iterable
from enum import Enum
from redis import Redis, ConnectionPool

from ..context import Context
from ..application import Application


__all__ = ["RedisPlugin", "RedisServ"]


class RedisKey(Enum):
    session = 1


class RedisPlugin:
    redis_pool: ConnectionPool
    patterns: Iterable[str]

    def __init__(self, host: str, port: int=6379, db: int=0, password: str=None, patterns: Iterable[str]=('.*',)):
        if password is None:
            self.redis_pool = ConnectionPool(host=host, port=port, db=db)
        else:
            self.redis_pool = ConnectionPool(host=host, port=port, db=db, password=password)
        self.patterns = patterns

    def processor(self, ctx: Context):
        ctx.box[RedisKey.session] = Redis(connection_pool=self.redis_pool)
        return ctx()

    def init_app(self, app: Application) -> None:
        for pattern in self.patterns:
            segs = pattern.split()
            if len(segs) == 1:
                app.add_interceptor(pattern, method='*', dealer=self.processor)
            elif len(segs) == 2:
                app.add_interceptor(segs[1], method=segs[0], dealer=self.processor)

    def teardown(self, exception: Exception) -> None:
        pass


class RedisServ:
    ctx: Context

    @property
    def redis(self) -> Redis:
        session = self.ctx.box.get(RedisKey.session)
        if session is None:
            raise ValueError('redis session not available')
        return session
