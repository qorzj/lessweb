from typing import Any
import sys
NEW_INSPECT = sys.version_info[:3] >= (3, 8, 0)
if NEW_INSPECT:
    from typing import Protocol  # since python3.8+
else:
    from typing_extensions import Protocol  # type: ignore


__all__ = ["PluginProto"]


class PluginProto(Protocol):
    def init_app(self, app: Any) -> None:
        ...

    def teardown(self, exception: Exception) -> None:
        ...
