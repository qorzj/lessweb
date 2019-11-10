from typing import Any
from enum import Enum
from redis import Redis, ConnectionPool

from ..context import Context
from ..model import Service


class RedisKey(Enum):
    session: int = ...


class GlobalData:
    redis_pool: Any


class RedisServ(Service):
    ctx: Context
    redis: Redis
    def __init__(self, ctx: Context) -> None: ...


global_data: GlobalData = ...


def init(host: str, port: int=..., db: int=...): ...
def processor(ctx: Context): ...
def session() -> Redis: ...
