from typing import Any, Dict, List, Union

from lessweb.bridge import Bridge


Jsonizable = Union[str, int, float, Dict, List, None]


class BaseBridge(Bridge):
    def __init__(self):
        pass

    def to(self)->Any:
        return ...


class JsonToJson(Bridge):
    def __init__(self, source: Jsonizable):
        self.value = source

    def to(self) -> Jsonizable:
        if isinstance(self.value, (str, int, float)) or self.value is None:
            return self.value

        if isinstance(self.value, list):
            return [self.cast(item, type(item), Jsonizable) for item in self.value]

        return {k: self.cast(v, type(v), Jsonizable) for (k, v) in self.value.items()}
