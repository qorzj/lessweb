"""lessweb: 用最python3的方法创建web apps"""


#__version__ = '0.2.5'
#__author__ = [
#    'qorzj <inull@qq.com>',
#]
#
#__license__ = "MIT"

from . import application, context, model, storage, webapi

from .application import (
    interceptor as interceptor,
    Application as Application,
)
from .context import (
    Context as Context,
    Request as Request,
    Response as Response,
)
from .storage import (
    Storage as Storage,
)
from .bridge import (
    uint as uint,
    ParamStr as ParamStr,
    MultipartFile as MultipartFile,
    Jsonizable as Jsonizable,
)
from .webapi import (
    BadParamError as BadParamError,
    NotFoundError as NotFoundError,
    Cookie as Cookie,
    HttpStatus as HttpStatus,
    ResponseStatus as ResponseStatus,
)
from .utils import (
    _nil as _nil,
    eafp as eafp,
)
