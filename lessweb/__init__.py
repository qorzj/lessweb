"""lessweb: 用最python3的方法创建web apps"""


__version__ = '0.3.0'
__author__ = [
    'qorzj <inull@qq.com>',
]

__license__ = "MIT"

# from . import application, context, model, storage, webapi

from .application import interceptor, Application
from .context import Context, Request, Response
from .model import Model, Service
from .storage import Storage
from .bridge import RequestBridge, uint, ParamStr, ParamSource, MultipartFile
from .typehint import issubtyping, AnySub
from .webapi import NeedParamError, BadParamError, NotFoundError, Cookie, HttpStatus, ResponseStatus
from .utils import _nil, eafp
