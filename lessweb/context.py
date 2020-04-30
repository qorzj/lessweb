from typing import Any, Optional, Dict, List, Union, TYPE_CHECKING
import cgi
import json
import os

from io import BytesIO
from requests.structures import CaseInsensitiveDict
from urllib.parse import unquote

from .storage import Storage
from .webapi import Cookie, HttpStatus, ResponseStatus, ParamInput
from .bridge import Jsonizable, ParamStr, MultipartFile
from .webapi import header_name_of_wsgi_key, wsgi_key_of_header_name
from .webapi import parse_cookie, mimetypes
from .utils import eafp


__all__ = ["Request", "Response", "Context"]


if TYPE_CHECKING:
    from lessweb.application import Application


class Request:
    """
    Contextual variables:
        * environ a.k.a. env – a dictionary containing the standard WSGI environment variables
        * home – the base path for the application, including any parts "consumed" by outer applications
        * homedomain – ? (appears to be protocol + host)
        * homepath – The part of the path requested by the user which was trimmed off the current app. That is homepath + path = the path actually requested in HTTP by the user. E.g. /admin This seems to be derived during startup from the environment variable REAL_SCRIPT_NAME. It affects what web.url() will prepend to supplied urls. This in turn affects where web.seeother() will go, which might interact badly with your url rewriting scheme (e.g. mod_rewrite)
        * host – the hostname (domain) and (if not default) the port requested by the user. E.g. example.org, example.org:8080
        * ip – the IP address of the user. E.g. xxx.xxx.xxx.xxx
        * method – the HTTP method used. E.g. POST
        * path – the path requested by the user, relative to the current application. If you are using subapplications, any part of the url matched by the outer application will be trimmed off. E.g. you have a main app in code.py, and a subapplication called admin.py. In code.py, you point /admin to admin.app. In admin.py, you point /stories to a class called stories. Within stories, web.ctx.path will be /stories, not /admin/stories.
        * protocol – the protocol used. E.g. https
        * query – an empty string if there are no query arguments otherwise a ? followed by the query string.
        * fullpath a.k.a. path + query – the path requested including query arguments but not including homepath.

        e.g. GET http://localhost:8080/api/hello/echo?a=1&b=2
            host => localhost:8080
            protocol => http
            homedomain => http://localhost:8080
            homepath => /api
            home => http://localhost:8080/api
            ip => 127.0.0.1
            method => GET
            path => /hello/echo
            query => a=1&b=2
            fullpath => /hello/echo?a=1&b=2

        lessweb use ctx.path in routing.
    """
    def __init__(self, encoding: str):
        self._cookies: Dict[str, str] = {}
        self._aliases: Dict[str, str] = {}  # alias {realname: queryname}
        self._params: Dict[str, Union[ParamStr, Jsonizable, None]] = {}

        self.encoding: str = encoding
        self.environ: Dict = {}
        self.env: Dict = {}
        self.host: str = ''
        self.protocol: str = ''
        self.homedomain: str = ''
        self.homepath: str = ''
        self.home: str = ''
        self.ip: str = ''
        self.method: str = ''
        self.path: str = ''  # ctx.path是路由的依据，因此是unquote之后的结果
        self.query: str = ''
        self.fullpath: str = ''

        self.body_data: Optional[bytes] = None  # Raw Body Input
        self.json_input: Optional[Jsonizable] = None  # Input from Json Body
        self.param_input: ParamInput = ParamInput()  # Param Inputs
        self.file_input: Dict[str, List[MultipartFile]] = {}  # Uploaded File Inputs

    def load(self, env):
        encoding = self.encoding
        request_uri = env.get('REQUEST_URI')
        self.environ = self.env = env
        self.host = env.get('HTTP_HOST', '[unknown]')
        if env.get('wsgi.url_scheme') in ['http', 'https']:
            self.protocol = env['wsgi.url_scheme']
        elif env.get('HTTPS', '').lower() in ['on', 'true', '1']:
            self.protocol = 'https'
        else:
            self.protocol = 'http'
        self.homedomain = self.protocol + '://' + self.host
        self.homepath = os.environ.get('REAL_SCRIPT_NAME', env.get('SCRIPT_NAME', ''))
        self.home = self.homedomain + self.homepath
        self.ip = env.get('REMOTE_ADDR', '0.0.0.0')
        self.method = env.get('REQUEST_METHOD', '')
        if request_uri is not None:
            self.path = unquote(request_uri.split('?', 1)[0][len(self.homepath):], encoding=encoding)
        else:
            self.path = env.get('PATH_INFO', '')  # you have to follow your server's default path encoding
        self.query = env.get('QUERY_STRING', '')
        self.fullpath = self.homedomain + (request_uri or '')
        # init cookie
        if not self._cookies and self.contains_header('cookie'):
            self._cookies = parse_cookie(self.get_header('cookie'))
        # parse query params
        self.param_input.load_query(self.query, encoding)
        # load body data
        cl = eafp(lambda: int(self.env.get('CONTENT_LENGTH')), 0)
        self.body_data = self.env['wsgi.input'].read(cl) if cl else None
        # parse form params
        if self.body_data:
            if self.is_json():
                self.json_input = eafp(lambda: json.loads(self.body_data.decode(encoding)),
                                       {'__error__': 'invalid json received'})
            elif self.is_form():
                eafp(lambda: self.param_input.load_form(self.body_data, self.env, encoding, self.file_input), None)


    def set_alias(self, realname, queryname):
        self._aliases[realname] = queryname

    def get_content_type(self) -> str:
        return self.env.get('CONTENT_TYPE', '')

    def is_json(self) -> bool:
        return 'json' in self.get_content_type().lower()

    def is_form(self) -> bool:
        content_type = self.get_content_type().lower()
        return bool(content_type) and ('form-' in content_type or '-urlencoded' in content_type)

    def contains_cookie(self, name: str) -> bool:
        return name in self._cookies

    def get_cookie(self, name: str) -> Optional[str]:
        return self._cookies.get(name)

    def get_cookienames(self) -> List[str]:
        return list(self._cookies.keys())

    def contains_header(self, name: str) -> bool:
        return wsgi_key_of_header_name(name) in self.env

    def get_header(self, name: str) -> Optional[str]:
        """
        根据http规范，多header应该合并入一个key/value，例如requests的headers就是dict。
        """
        return self.env.get(wsgi_key_of_header_name(name))

    def get_headernames(self) -> List[str]:
        return [s for s in (header_name_of_wsgi_key(k) for k in self.env.keys()) if s]

    def get_auth_bearer(self) -> Optional[str]:
        header_val = self.get_header('Authorization')
        if header_val is None:
            return None
        return header_val[len('Bearer '):]

    def get_input(self, key: str) -> Optional[Union[ParamStr, Jsonizable]]:
        # 注意cgi不保证重名参数的顺序，如果每次请求得到的结果可能不同
        if key in self._params:
            return self._params[key]
        param = self.param_input
        ret: Optional[Union[ParamStr, Jsonizable]]
        if key in param.url_input:
            self._params[key] = ret = param.url_input[key]
        elif key in param.form_input:  # must in front of query_input
            self._params[key] = ret = param.form_input[key][0]
        elif key in param.query_input:
            self._params[key] = ret = param.query_input[key][0]
        elif isinstance(self.json_input, dict):
            self._params[key] = ret = self.json_input.get(key, None)
        else:
            self._params[key] = ret = None
        return ret

    def get_uploaded_files(self, key: str) -> List[MultipartFile]:
        return self.file_input.get(key, [])


class Response:
    def __init__(self, encoding: str):
        self._cookies: Dict[str, Cookie] = {}
        self._status: Union[HttpStatus, ResponseStatus] = HttpStatus.OK
        self._headers: CaseInsensitiveDict = CaseInsensitiveDict()
        self.encoding: str = encoding

    def set_cookie(self, name:str, value:str, expires:int=None, path:str='/',
                   domain:str=None, secure:bool=False, httponly:bool=False) -> None:
        self._cookies[name] = Cookie(name, value, expires, path, domain, secure, httponly)

    def get_cookie(self, name:str) -> Optional[Cookie]:
        return self._cookies.get(name)

    def del_cookie(self, name:str) -> None:
        self._cookies.pop(name, None)

    def set_status(self, status: Union[HttpStatus, ResponseStatus]) -> None:
        self._status = status

    def get_status(self) -> Union[HttpStatus, ResponseStatus]:
        return self._status

    def set_header(self, name: str, value: Union[str, int]) -> None:
        if isinstance(value, int):
            self._headers[name] = str(value)
        elif '\n' in name or '\r' in name or '\n' in value or '\r' in value:
            raise ValueError('invalid characters in header')
        else:
            self._headers[name] = value

    def get_header(self, name: str) -> Optional[str]:
        return self._headers.get(name)

    def del_header(self, name: str) -> str:
        return self._headers.pop(name, None)

    def get_headernames(self) -> List[str]:
        return list(self._headers.keys())

    def clear(self) -> None:
        """
        Clear headers and cookies.
        """
        self._headers.clear()
        self._cookies.clear()

    def send_access_allow(self, allow_headers: List[str]=None) -> None:
        allow_headers = allow_headers or []
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers',
                        'Cache-Control, Accept-Encoding, Origin, X-Requested-With, Content-Type, Accept, '
                        'Authorization, Referer, User-Agent' + ''.join(', '+h for h in allow_headers))

    def send_allow_methods(self, methods: List[str]):
        self.set_header('Allow', ', '.join(methods))

    def send_redirect(self, location: str) -> None:
        self.set_header('Location', location)

    def send_content_type(self, mimekey='html', encoding: str=''):
        mimekey = mimekey.lower()
        if encoding:
            self.set_header('Content-Type', '%s; charset=%s' % (mimetypes[mimekey], encoding))
        else:
            self.set_header('Content-Type', '%s' % mimetypes[mimekey])


class Context(object):
    def __init__(self, app: 'Application') -> None:
        self.app_stack: List = []
        self.app: Application = app
        self.request: Request = Request(app.encoding)
        self.response: Response = Response(app.encoding)
        self.box: Dict = {}

    def __call__(self):
        return self.app_stack[-1](self)

