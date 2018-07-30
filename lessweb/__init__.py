"""lessweb: 用最python3的方法创建web apps"""


__version__ = '0.1.27'
__author__ = [
    'qorzj <inull@qq.com>',
]

__license__ = "MIT"

from . import application, context, model, storage, webapi

from .application import interceptor, Application
from .context import Context
from .model import get_annotations, get_func_parameters, get_model_parameters, Model
from .model import RestParam, Jsonable
from .storage import Storage
from .webapi import HttpError, MovedPermanently, Found, SeeOther, NotModified, TempRedirect, \
    BadRequest, Unauthorized, Forbidden, NotFound, NoMethod, NotAcceptable, Conflict, Gone, \
    PreconditionFailed, UnsupportedMediaType, UnavailableForLegalReasons, InternalError
from .webapi import UploadedFile, status_table, NeedParamError, BadParamError
from .utils import _nil, Service, eafp, json_dumps, ChainMock
