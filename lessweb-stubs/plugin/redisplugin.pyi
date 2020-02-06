from typing import Iterable, Any
from enum import Enum
from redis import Redis, ConnectionPool

from lessweb.context import Context
from lessweb.model import Service
from lessweb.application import Application


__all__ = ["RedisPlugin", "RedisServ"]


class RedisKey(Enum):
    session: int = ...


class RedisPlugin:
    def __init__(self, host: str, port:int=..., db:int=..., patterns: Iterable[str]=...) -> None: ...
    def processor(self, ctx: Context) -> Any: ...
    def init_app(self, app: Application) -> None: ...
    def teardown(self, exception: Exception) -> None: ...


class RedisServ(Service):
    ctx: Context
    redis: Redis
    def __init__(self, ctx: Context) -> None: ...