from typing import Optional, Dict, List, Union
import cgi
import json

from io import BytesIO
from requests.structures import CaseInsensitiveDict

from lessweb.storage import Storage
from lessweb.webapi import UploadedFile, Cookie, HttpStatus
from lessweb.webapi import header_name_of_wsgi_key, wsgi_key_of_header_name
from lessweb.webapi import parse_cookie, mimetypes
from lessweb.utils import fields_in_query
from lessweb.garage import Jsonizable


def _process_fieldstorage(fs):
    if isinstance(fs, list):
        return _process_fieldstorage(fs[0])  # 递归计算
    elif fs.filename is None:  # 非文件参数
        return fs.value
    else:  # 文件参数
        return UploadedFile(fs)


def _dictify(fs):
    # hack to make input work with enctype='text/plain.
    if fs.list is None:
        fs.list = []
    return dict([(k, _process_fieldstorage(fs[k])) for k in fs.keys()])


class Request:
    def __init__(self):
        self.env: Dict = {}
        self._cookies: Dict[str, str] = {}

    def _init_cookies(self):
        if not self._cookies and self.contains_header('cookie'):
            self._cookies = parse_cookie(self.get_header('cookie'))

    def contains_cookie(self, name: str) -> bool:
        self._init_cookies()
        return name in self._cookies

    def get_cookie(self, name: str) -> Optional[str]:
        self._init_cookies()
        return self._cookies.get(name)

    def get_cookienames(self) -> List[str]:
        self._init_cookies()
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


class Response:
    def __init__(self):
        self._cookies: Dict[str, Cookie] = {}
        self._status: HttpStatus = HttpStatus.OK
        self._headers = CaseInsensitiveDict()

    def set_cookie(self, name:str, value:str, expires:int=None, path:str='/',
                   domain:str=None, secure:bool=False, httponly:bool=False) -> None:
        self._cookies[name] = Cookie(name, value, expires, path, domain, secure, httponly)

    def get_cookie(self, name:str) -> Optional[Cookie]:
        return self._cookies.get(name)

    def del_cookie(self, name:str) -> None:
        self._cookies.pop(name, None)

    def set_status(self, status: HttpStatus) -> None:
        self._status = status

    def get_status(self) -> HttpStatus:
        return self._status

    def set_header(self, name: str, value: Union[str, int]) -> None:
        if '\n' in name or '\r' in name or '\n' in value or '\r' in value:
            raise ValueError('invalid characters in header')
        self._headers[name] = str(value)

    def get_header(self, name: str) -> Optional[str]:
        return self._headers.get(name)

    def del_header(self, name: str) -> None:
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
            home,realhome => http://localhost:8080/api
            ip => 127.0.0.1
            method => GET
            path => /hello/echo
            query => a=1&b=2
            fullpath => /hello/echo?a=1&b=2

        lessweb use ctx.path in routing.
    """
    def __init__(self, app=None) -> None:
        self.app_stack: List = []
        self.app = app
        self.view = None
        self._aliases: Dict[str, str] = {}  # alias {realname: queryname}

        self._url_input: Dict = {}  # Input from URL
        self._json_input: Optional[Dict] = None  # Input from Json Body
        self._post_data: Optional[Dict] = None  # Raw Body Input
        self._fields: Optional[Dict] = None  # Input from Json Body and Form Fields
        self._pipe: Storage = Storage()

        self.environ: Dict = {}
        self.env: Dict = {}
        self.host: str = ''
        self.protocol: str = ''
        self.homedomain: str = ''
        self.homepath: str = ''
        self.home: str = ''
        self.realhome: str = ''
        self.ip: str = ''
        self.method: str = ''
        self.path: str = ''
        self.query: str = ''
        self.fullpath: str = ''
        self.request: Request = Request()
        self.response: Response = Response()

    @property
    def _field_input(self)->Dict:  # Input from Form
        if self._json_input is not None:
            return self._json_input
        if self._fields is not None:
            return self._fields
        if self.is_json_request() and self.body_data():
            try:
                self._json_input = json.loads(self.body_data().decode(self.app.encoding))
            except:
                self._json_input = {'__error__': 'invalid json received'}
            if not isinstance(self._json_input, dict):
                self._json_input = {'__error__': 'invalid json received (not dict)'}
            return self._json_input
        else:
            try:
                if self.method in ['HEAD', 'DELETE']:
                    self._fields = fields_in_query(self.query)
                    return self._fields

                # cgi.FieldStorage can raise exception when handle some input
                if self.method == 'GET':
                    _ = cgi.FieldStorage(environ=self.env.copy(), keep_blank_values=1)
                else:
                    fp = BytesIO(self.body_data())
                    _ = cgi.FieldStorage(fp=fp, environ=self.env.copy(), keep_blank_values=1)
                self._fields = _dictify(_)
            except:
                self._fields = {'__error__': 'invalid form data received'}
        return self._fields

    def __call__(self):
        return self.app_stack[-1](self)

    def set_param(self, realname, realvalue):
        self._pipe[realname] = realvalue

    def get_param(self, realname, default=None):
        return self._pipe.get(realname, default)

    def set_alias(self, realname, queryname):
        self._aliases[realname] = queryname

    def is_json_request(self):
        return self._json_input is not None or \
               'json' in self.env.get('CONTENT_TYPE', '').lower()

    def body_data(self) -> bytes:
        if self._post_data is not None:
            return self._post_data
        try:
            cl = int(self.env.get('CONTENT_LENGTH'))
        except:
            cl = 0
        self._post_data = self.env['wsgi.input'].read(cl)
        return self._post_data

    def get_input(self, queryname, default=None)->Jsonizable:
        return self._url_input[queryname] if queryname in self._url_input else \
            self._field_input.get(queryname, default)

    def get_inputs(self)->Dict[str, Jsonizable]:
        return {**self._field_input, **self._url_input}
