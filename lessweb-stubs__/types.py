from typing import Dict, List, Union
from enum import Enum


Jsonizable = Union[str, int, float, Dict, List, None]


class ParamSource(Enum):
    Url = 1
    Query = 2
    Form = 3
    Env = 4


class ParamStr:
    value: str
    source: ParamSource
