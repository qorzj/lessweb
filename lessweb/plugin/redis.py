from typing import Any
from redis import Redis, Connection

from ..context import Context


class GlobalData:
    redis_pool: Any


global_data = GlobalData()


class RedisCtx(Context):
    redis: Redis


def init(host, port, db=0):
    global_data.redis_pool = Connection(host=host, port=port, db=db)


def processor(ctx: RedisCtx):
    ctx.redis = Redis(connection_pool=global_data.redis_pool)
