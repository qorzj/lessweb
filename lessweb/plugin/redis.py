from typing import Any
from redis import Redis, ConnectionPool

from ..context import Context


class GlobalData:
    redis_pool: Any


global_data = GlobalData()


class RedisCtx(Context):
    redis: Redis


def init(host, port, db=0):
    global_data.redis_pool = ConnectionPool(host=host, port=port, db=db)


def processor(ctx: RedisCtx):
    ctx.redis = session()
    return ctx()


def session():
    return Redis(connection_pool=global_data.redis_pool)
