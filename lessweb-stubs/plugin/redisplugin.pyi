from typing import Iterable, Any
from enum import Enum
from redis import Redis, ConnectionPool

from lessweb.context import Context
from lessweb.application import Application


__all__ = ["RedisPlugin", "RedisServ"]


class RedisKey(Enum):
    session: int = ...


class RedisPlugin:
    redis_pool: ConnectionPool
    patterns: Iterable[str]
    def __init__(self, host: str, port:int=..., db:int=..., password: str=..., patterns: Iterable[str]=...) -> None: ...
    def processor(self, ctx: Context) -> Any: ...
    def init_app(self, app: Application) -> None: ...
    def teardown(self, exception: Exception) -> None: ...


class RedisServ:
    ctx: Context
    @property
    def redis(self) -> Redis: ...