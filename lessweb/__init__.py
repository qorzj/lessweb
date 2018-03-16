"""lessweb: 用最python3的方法创建web apps"""


from .webapi import HttpError

__version__ = '0.1.7'
__author__ = [
    'qorzj <inull@qq.com>',
]

__license__ = "public domain"

from . import application, context, model, storage, webapi

from .application import interceptor, Application
from .context import Context
from .model import rest_param, tips, get_tips, get_annotations
from .model import get_func_parameters, get_model_parameters, Model
from .storage import Storage
from .webapi import HttpError, Found, SeeOther, NotModified, TempRedirect, \
    BadRequest, Unauthorized, Forbidden, NotFound, NoMethod, NotAcceptable, Conflict, Gone, \
    PreconditionFailed, UnsupportedMediaType, UnavailableForLegalReasons, InternalError
from .webapi import status_table, NeedParamError, BadParamError
from .utils import eafp, json_dumps