from typing import Any
from enum import Enum
from redis import Redis, ConnectionPool

from ..context import Context
from ..model import Service


class RedisKey(Enum):
    session = 1


class GlobalData:
    redis_pool: Any


class RedisServ(Service):
    ctx: Context
    redis: Redis

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.redis = ctx.get_param(RedisKey.session)


global_data = GlobalData()


def init(host, port=6379, db=0):
    global_data.redis_pool = ConnectionPool(host=host, port=port, db=db)


def processor(ctx: Context):
    ctx.set_param(RedisKey.session, session())
    return ctx()


def session() -> Redis:
    return Redis(connection_pool=global_data.redis_pool)
