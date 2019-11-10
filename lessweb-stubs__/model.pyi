from typing import Callable, Optional, Type, Dict
from abc import ABCMeta

from lessweb.context import Context, Request, Response
from lessweb.webapi import NeedParamError, BadParamError, UploadedFile
from lessweb.typehint import generic_origin
from lessweb.garage import BaseBridge, Jsonizable
from lessweb.bridge import Bridge
from lessweb.utils import func_arg_spec
from lessweb.storage import Storage


class Model(metaclass=ABCMeta):
    def __eq__(self, other): ...
    def __repr__(self): ...


class Service(metaclass=ABCMeta):
    ...


def fetch_service(ctx: Context, service_type: Type): ...
def fetch_model(ctx: Context, model_type: Type[Model]): ...
def fetch_param(ctx: Context, fn: Callable) -> Dict: ...


class ModelToDict(Bridge):
    def __init__(self, source: Model) -> None: ...
    def to(self) -> Jsonizable: ...
