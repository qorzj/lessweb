from typing import Any, Dict, List, Union, NamedTuple
from typing import get_type_hints

from lessweb.bridge import Bridge
from lessweb.model import Model


Jsonizable = Union[str, int, float, Dict, List, None]


class BaseBridge(Bridge):
    def of(self, source: Any):
        pass

    def to(self)->Any:
        return ...


class ModelToDict(Bridge):
    value: Model

    def of(self, source: Model):
        self.value = source

    def to(self) -> Jsonizable:
        ret = {}
        for name, type_ in get_type_hints(type(self.value)).items():
            if hasattr(self.value, name):
                value = self.cast(getattr(self.value, name), type_, Jsonizable)
                ret[name] = value
        return ret


class JsonToJson(Bridge):
    value: Jsonizable

    def of(self, source: Jsonizable):
        self.value = source

    def to(self) -> Jsonizable:
        if isinstance(self.value, (str, int, float)):
            return self.value

        if isinstance(self.value, list):
            return [self.cast(item, type(item), Jsonizable) for item in self.value]

        return {k: self.cast(v, type(v), Jsonizable) for (k, v) in self.value.items()}
