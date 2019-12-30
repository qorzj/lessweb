from typing import Any
try:
    from typing import Protocol  # since python3.8+
except ImportError:
    from typing_extensions import Protocol


__all__ = ["PluginProto"]


class PluginProto(Protocol):
    def init_app(self, app: Any) -> None:
        ...

    def teardown(self, exception: Exception) -> None:
        ...
