from enum import Enum
from redis import Redis, ConnectionPool

from ..context import Context
from ..model import Service
from ..application import Application


__all__ = ["RedisPlugin", "RedisServ"]


class RedisKey(Enum):
    session = 1


class RedisPlugin:
    def __init__(self, host, port=6379, db=0, patterns=('.*',)):
        self.redis_pool = ConnectionPool(host=host, port=port, db=db)
        self.patterns = patterns

    def processor(self, ctx: Context):
        ctx.box[RedisKey.session] = Redis(connection_pool=self.redis_pool)
        return ctx()

    def init_app(self, app: Application):
        for pattern in self.patterns:
            segs = pattern.split()
            if len(segs) == 1:
                app.add_interceptor(pattern, method='*', dealer=self.processor)
            elif len(segs) == 2:
                app.add_interceptor(segs[1], method=segs[0], dealer=self.processor)

    def teardown(self, exception: Exception):
        pass


class RedisServ(Service):
    ctx: Context
    redis: Redis

    def __init__(self, ctx: Context):
        self.ctx = ctx
        session = ctx.box.get(RedisKey.session)
        if session is None:
            raise ValueError('redis session not available')
        self.redis = session
