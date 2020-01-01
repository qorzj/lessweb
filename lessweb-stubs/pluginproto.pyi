from typing import Any
from typing_extensions import Protocol


__all__ = ["PluginProto"]


class PluginProto(Protocol):
    def init_app(self, app: Any) -> None: ...
    def teardown(self, exception: Exception) -> None: ...
