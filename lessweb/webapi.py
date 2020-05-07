from typing import Optional, Dict, List
import cgi
from io import BytesIO
from http.cookies import Morsel, SimpleCookie, CookieError
from urllib.parse import parse_qs, unquote
from enum import Enum
from typing import NamedTuple
from .bridge import ParamStr, MultipartFile


__all__ = ["mimetypes", "hop_by_hop_headers", "http_methods", "ParamInput", "ResponseStatus", "HttpStatus",
           "Cookie", "parse_cookie", "BadParamError", "NotFoundError"]


mimetypes = {
    "html": "text/html", "tcl": "application/x-tcl", "mov": "video/quicktime", "xpi": "application/x-xpinstall", "ogg": "audio/ogg", "exe": "application/octet-stream", "wmlc": "application/vnd.wap.wmlc", "ear": "application/java-archive", "m4v": "video/x-m4v", "jnlp": "application/x-java-jnlp-file", "jpg": "image/jpeg", "m4a": "audio/x-m4a", "jar": "application/java-archive", "rss": "application/rss+xml", "woff": "application/font-woff", "css": "text/css", "mml": "text/mathml", "crt": "application/x-x509-ca-cert", "mng": "video/x-mng", "mp3": "audio/mpeg", "tif": "image/tiff", "pl": "application/x-perl", "dll": "application/octet-stream", "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "asf": "video/x-ms-asf", "eps": "application/postscript", "iso": "application/octet-stream", "swf": "application/x-shockwave-flash", "wml": "text/vnd.wap.wml", "txt": "text/plain", "svgz": "image/svg+xml", "jng": "image/x-jng", "war": "application/java-archive", "webp": "image/webp", "bin": "application/octet-stream", "xls": "application/vnd.ms-excel", "htm": "text/html", "atom": "application/atom+xml", "sit": "application/x-stuffit", "sea": "application/x-sea", "7z": "application/x-7z-compressed", "hqx": "application/mac-binhex40", "pdb": "application/x-pilot", "asx": "video/x-ms-asf", "run": "application/x-makeself", "jad": "text/vnd.sun.j2me.app-descriptor", "img": "application/octet-stream", "ico": "image/x-icon", "tiff": "image/tiff", "pm": "application/x-perl", "jpeg": "image/jpeg", "shtml": "text/html", "ts": "video/mp2t", "flv": "video/x-flv", "pdf": "application/pdf", "mpg": "video/mpeg", "xml": "text/xml", "wbmp": "image/vnd.wap.wbmp", "msm": "application/octet-stream", "json": "application/json", "zip": "application/zip", "ai": "application/postscript", "ppt": "application/vnd.ms-powerpoint", "msp": "application/octet-stream", "kml": "application/vnd.google-earth.kml+xml", "msi": "application/octet-stream", "dmg": "application/octet-stream", "rtf": "application/rtf", "gif": "image/gif", "tk": "application/x-tcl", "mp4": "video/mp4", "js": "application/javascript", "mpeg": "video/mpeg", "pem": "application/x-x509-ca-cert", "rpm": "application/x-redhat-package-manager", "htc": "text/x-component", "m3u8": "application/vnd.apple.mpegurl", "bmp": "image/x-ms-bmp", "png": "image/png", "der": "application/x-x509-ca-cert", "ra": "audio/x-realaudio", "eot": "application/vnd.ms-fontobject", "prc": "application/x-pilot", "webm": "video/webm", "midi": "audio/midi", "kmz": "application/vnd.google-earth.kmz", "doc": "application/msword", "mid": "audio/midi", "xspf": "application/xspf+xml", "avi": "video/x-msvideo", "wmv": "video/x-ms-wmv", "kar": "audio/midi", "3gpp": "video/3gpp", "cco": "application/x-cocoa", "svg": "image/svg+xml", "jardiff": "application/x-java-archive-diff", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "ps": "application/postscript", "xhtml": "application/xhtml+xml", "deb": "application/octet-stream", "3gp": "video/3gpp", "rar": "application/x-rar-compressed",
}

hop_by_hop_headers = (
    'Connection',
    'Keep-Alive',
    'Proxy-Authenticate',
    'Proxy-Authorization',
    'TE',
    'Trailers',
    'Transfer-Encoding',
    'Upgrade',
)

http_methods = (
    'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH',
)


class ParamInput:
    def __init__(self):
        self.url_input: Dict[str, ParamStr] = {}  # Input from URL
        self.query_input: Dict[str, List[ParamStr]] = {}  # Input from Query
        self.form_input: Dict[str, List[ParamStr]] = {}  # Input from Form. form_input contains query_input

    def load_query(self, query: str, encoding: str) -> None:
        if query and query[0] == '?':
            query = query[1:]
        parse_ret = parse_qs(query, keep_blank_values=True, encoding=encoding)
        for key, vals in parse_ret.items():
            self.query_input.setdefault(key, [])
            self.query_input[key].extend(ParamStr(val) for val in vals)

    def load_form(self, body: bytes, env: Dict, encoding: str, file_input: Dict[str, List[MultipartFile]]) -> None:
        parse_ret = cgi.FieldStorage(fp=BytesIO(body), environ=env.copy(), keep_blank_values=1, encoding=encoding)
        if parse_ret.list is None: # hack to make input work with enctype='text/plain.
            parse_ret.list = []
        for key in parse_ret.keys():
            val = parse_ret[key]
            for item in (val if isinstance(val, list) else [val]):
                if item.filename is None:  # 非文件
                    self.form_input.setdefault(key, [])
                    self.form_input[key].append(ParamStr(item.value))
                else:  # 文件
                    file_input.setdefault(key, [])
                    file_input[key].append(MultipartFile(item))

    def load_url(self, groupdict: Dict) -> None:
        for key, val in groupdict.items():
            self.url_input[key] = ParamStr(val)


class ResponseStatus(NamedTuple):
    code: int
    reason: str


class HttpStatus(Enum):
    @staticmethod
    def of(code: int) -> 'HttpStatus':
        for status in HttpStatus:
            if status.value.code == code:
                return status
        raise NotImplementedError(f'HTTP status {code} is not implemented.')

    OK = ResponseStatus(code=200, reason='OK')
    Created = ResponseStatus(code=201, reason='Created')
    Accepted = ResponseStatus(code=202, reason='Accepted')
    NoContent = ResponseStatus(code=204, reason='No Content')
    MovedPermanently = ResponseStatus(code=301, reason='Moved Permanently')
    Found = ResponseStatus(code=302, reason='Found')
    SeeOther = ResponseStatus(code=303, reason='See Other')
    NotModified = ResponseStatus(code=304, reason='Not Modified')
    TemporaryRedirect = ResponseStatus(code=307, reason='Temporary Redirect')
    BadRequest = ResponseStatus(code=400, reason='Bad Request')
    Unauthorized = ResponseStatus(code=401, reason='Unauthorized')
    Forbidden = ResponseStatus(code=403, reason='Forbidden')
    NotFound = ResponseStatus(code=404, reason='Not Found')
    MethodNotAllowed = ResponseStatus(code=405, reason='Method Not Allowed')
    NotAcceptable = ResponseStatus(code=406, reason='Not Acceptable')
    Conflict = ResponseStatus(code=409, reason='Conflict')
    Gone = ResponseStatus(code=410, reason='Gone')
    PreconditionFailed = ResponseStatus(code=412, reason='Precondition Failed')
    UnsupportedMediaType = ResponseStatus(code=415, reason='Unsupported Media Type')
    UnprocessableEntity = ResponseStatus(code=422, reason='Unprocessable Entity')
    UnavailableForLegalReasons = ResponseStatus(code=451, reason='Unavailable For Legal Reasons')
    InternalServerError = ResponseStatus(code=500, reason='Internal Server Error')


class Cookie:
    name: str
    value: str
    expires: Optional[int]
    path: str
    domain: Optional[str]
    secure: bool
    httponly: bool

    def __init__(self, name:str, value:str, expires:int=None, path:str='/',
                 domain:str=None, secure:bool=False, httponly:bool=False):
        self.name = name
        self.value = value
        self.expires = expires
        self.path = path
        self.domain = domain
        self.secure = secure
        self.httponly = httponly

    def dumps(self):
        morsel = Morsel()
        morsel.set(self.name, self.value, self.value)
        morsel['expires'] = '' if self.expires is None else self.expires
        morsel['path'] = self.path
        if self.domain: morsel['domain'] = self.domain
        if self.secure: morsel['secure'] = self.secure
        ret = morsel.OutputString()
        if self.httponly: ret += '; httponly'
        return ret


def parse_cookie(http_cookie: str)->Dict[str, str]:
    """Parse from cookie header string to Dict"""
    cookie: SimpleCookie = SimpleCookie()
    try:
        cookie.load(http_cookie)
    except CookieError:
        cookie = SimpleCookie()
        for attr_value in http_cookie.split(';'):
            try:
                cookie.load(attr_value)
            except CookieError:
                pass
    cookies = dict([(k, v.value) for k, v in cookie.items()])
    return cookies


class BadParamError(Exception):
    def __init__(self, message: str, param: str=''):
        self.param: str = param
        self.message: str = message

    def __repr__(self):
        return 'lessweb.BadParamError param:%s message:%s' % (self.param, self.message)

    def __str__(self):
        return self.message


class NotFoundError(Exception):
    def __init__(self, methods=None):
        self.methods = methods or []

    def __repr__(self):
        return 'Method Not Allowed' if self.methods else 'Not Found'

    def __str__(self):
        return 'Method Not Allowed' if self.methods else 'Not Found'


def header_name_of_wsgi_key(wsgi_key: str) -> str:
    """
    >>> header_name_of_wsgi_key('HTTP_ACCEPT_LANGUAGE')
    'Accept-Language'
    >>> header_name_of_wsgi_key('HTTP_AUTHORIZATION')
    'Authorization'

    """
    if wsgi_key.startswith('HTTP_'):
        words_for_short = {'IM', 'HTTP2', 'MD5', 'TE', 'DNT', 'ATT', 'UIDH', 'XSS'}
        return '-'.join((s if s in words_for_short else s.capitalize()) for s in wsgi_key[5:].split('_'))
    else:
        return ''


def wsgi_key_of_header_name(header_name: str) -> str:
    """
    >>> wsgi_key_of_header_name('Accept-Language')
    'HTTP_ACCEPT_LANGUAGE'
    >>> wsgi_key_of_header_name('Authorization')
    'HTTP_AUTHORIZATION'

    """
    return 'HTTP_' + header_name.replace('-', '_').upper()