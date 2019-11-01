from typing import Any, Dict, List, Union


Jsonizable = Union[str, int, float, Dict, List, None]


class BaseBridge(Bridge):
    def __init__(self) -> None: ...
    def to(self)->Any: ...


class JsonToJson(Bridge):
    def __init__(self, source: Jsonizable) -> None: ...
    def to(self) -> Jsonizable: ...
