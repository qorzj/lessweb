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
from .model import (
    Model as Model,
    Service as Service,
)
from .storage import (
    Storage as Storage,
    ChainMock as ChainMock,
)
from .bridge import (
    Bridge as Bridge,
)
from .typehint import (
    issubtyping as issubtyping,
    AnySub as AnySub,
)
from .garage import (
    Jsonizable as Jsonizable,
)
from .webapi import (
    NeedParamError as NeedParamError,
    BadParamError as BadParamError,
    NotFoundError as NotFoundError,
    UploadedFile as UploadedFile,
    Cookie as Cookie,
    HttpStatus as HttpStatus,
)
from .utils import (
    _nil as _nil,
    eafp as eafp,
)
