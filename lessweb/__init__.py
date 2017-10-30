"""salar.py: 用最python3的方法创建web apps"""

from .application import application
from .webapi import HttpError

__version__ = '0.0.1'
__author__ = [
    'qorzj <inull@qq.com>',
]

__license__ = "public domain"

from . import application, context, model, storage, webapi

from .application import interceptor, application
from .context import Context
from .model import rest_param, need_param, choose_param, tips, get_tips, get_annotations
from .model import get_func_parameters, get_model_parameters, Model
from .storage import Storage, global_data
from .webapi import HttpError, BadRequestError, NeedParamError, BadParamError
