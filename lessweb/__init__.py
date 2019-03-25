"""lessweb: 用最python3的方法创建web apps"""


__version__ = '0.2.5'
__author__ = [
    'qorzj <inull@qq.com>',
]

__license__ = "MIT"

from . import application, context, model, storage, webapi

from .application import interceptor, Application
from .context import Context, Request, Response
from .model import Model, Service
from .storage import Storage, ChainMock
from .bridge import Bridge
from .typehint import issubtyping, AnySub
from .garage import Jsonizable
from .webapi import NeedParamError, BadParamError, NotFoundError, UploadedFile, Cookie, HttpStatus
from .utils import _nil, eafp
