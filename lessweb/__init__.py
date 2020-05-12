"""lessweb: 用最python3的方法创建web apps"""


__version__ = '0.3.1'
__author__ = [
    'qorzj <inull@qq.com>',
]

__license__ = "MIT"

# from . import application, context, model, storage, webapi

from .application import interceptor, Application
from .context import Context, Request, Response
from .storage import Storage
from .bridge import uint, ParamStr, MultipartFile, Jsonizable
from .webapi import BadParamError, NotFoundError, Cookie, HttpStatus, ResponseStatus
from .utils import _nil, eafp
