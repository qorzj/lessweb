from http.cookies import Morsel, SimpleCookie, CookieError
from urllib.parse import unquote, quote


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

status_table = {
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    204: 'No Content',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    307: 'Temporary Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    409: 'Conflict',
    410: 'Gone',
    412: 'Precondition Failed',
    415: 'Unsupported Media Type',
    422: 'Unprocessable Entity',
    451: 'Unavailable For Legal Reasons',
    500: 'Internal Server Error',
}


class UploadedFile:
    def __init__(self, upfile):
        self.filename = upfile.filename
        self.value = upfile.value


# HTTPError and subclasses
class HttpError(Exception):
    def __init__(self, *, status_code, text, headers=None):
        self.status_code: int = status_code
        self.text: str = text
        self.headers = headers or []

    @property
    def reason(self):
        return status_table.get(self.status_code, 'Other Error')


class _Redirect(HttpError):
    def __init__(self, status_code, fullurl, headers):
        headers = headers or []
        set_header(headers, 'Content-Type', 'text/html', setdefault=True)
        set_header(headers, 'Location', fullurl, setdefault=True)
        super().__init__(status_code=status_code, text='', headers=headers)


class MovedPermanently(_Redirect):
    def __init__(self, url, headers=None):
        headers = headers or []
        super().__init__(status_code=301, fullurl=url, headers=headers)


class Found(_Redirect):
    def __init__(self, url, headers=None):
        headers = headers or []
        super().__init__(status_code=302, fullurl=url, headers=headers)


class SeeOther(_Redirect):
    def __init__(self, url, headers=None):
        headers = headers or []
        super().__init__(status_code=303, fullurl=url, headers=headers)


class NotModified(HttpError):
    def __init__(self):
        super().__init__(status_code=304, text='')


class TempRedirect(_Redirect):
    def __init__(self, url, headers=None):
        super().__init__(status_code=307, fullurl=url, headers=headers)


class _TextHttpError(HttpError):
    def __init__(self, status_code, text, headers):
        headers = headers or []
        set_header(headers, 'Content-Type', 'text/html', setdefault=True)
        super().__init__(status_code=status_code, text=text, headers=headers)


class BadRequest(_TextHttpError):
    def __init__(self, text, headers=None):
        super().__init__(status_code=400, text=text, headers=headers)


class Unauthorized(_TextHttpError):
    def __init__(self, text='unauthorized', headers=None):
        super().__init__(status_code=401, text=text, headers=headers)


class Forbidden(_TextHttpError):
    def __init__(self, text="forbidden", headers=None):
        super().__init__(status_code=403, text=text, headers=headers)


class NotFound(HttpError):
    def __init__(self, text, headers=None):
        headers = headers or []
        set_header(headers, 'Content-Type', 'text/html', setdefault=True)
        super().__init__(status_code=404, text=text, headers=headers)


class NoMethod(_TextHttpError):
    def __init__(self, text='', methods=None and ['GET', ...], headers=None):
        headers = headers or []
        if methods:
            set_header(headers, 'Allow', ', '.join(methods), setdefault=True)
        super().__init__(status_code=405, text=text, headers=headers)


class NotAcceptable(_TextHttpError):
    def __init__(self, text='not acceptable', headers=None):
        super().__init__(status_code=406, text=text, headers=headers)


class Conflict(_TextHttpError):
    def __init__(self, text='conflict', headers=None):
        super().__init__(status_code=409, text=text, headers=headers)


class Gone(_TextHttpError):
    def __init__(self, text='gone', headers=None):
        super().__init__(status_code=410, text=text, headers=headers)


class PreconditionFailed(_TextHttpError):
    def __init__(self, text='precondition failed', headers=None):
        super().__init__(status_code=412, text=text, headers=headers)


class UnsupportedMediaType(_TextHttpError):
    def __init__(self, text='unsupported media type', headers=None):
        super().__init__(status_code=415, text=text, headers=headers)


class UnavailableForLegalReasons(_TextHttpError):
    def __init__(self, text='unavailable for legal reasons', headers=None):
        super().__init__(status_code=451, text=text, headers=headers)


class InternalError(_TextHttpError):
    def __init__(self, text='internal server error', headers=None):
        super().__init__(status_code=500, text=text, headers=headers)


def set_header(headers, key, value, multiple=False, setdefault=False):
    assert isinstance(key, str) and isinstance(value, str)
    if '\n' in key or '\r' in key or '\n' in value or '\r' in value:
        raise ValueError('invalid characters in header')
    if not multiple:
        for idx, (k, v) in enumerate(headers):
            if k.lower() == key.lower():
                if not setdefault:
                    headers[idx] = (key, value)
                return
    headers.append((key, value))


def make_cookie(name, value, expires='', path='', domain=None, secure=False, httponly=False):
    """Make a cookie string"""
    morsel = Morsel()
    morsel.set(name, value, quote(value))
    if isinstance(expires, int) and expires < 0:
        expires = -1000000000
    morsel['expires'] = expires
    morsel['path'] = path
    if domain: morsel['domain'] = domain
    if secure: morsel['secure'] = secure
    value = morsel.OutputString()
    if httponly: value += '; httponly'
    return value


def parse_cookie(http_cookie):
    """Parse from cookie header string to Dict"""
    cookie = SimpleCookie()
    try:
        cookie.load(http_cookie)
    except CookieError:
        cookie = SimpleCookie()
        for attr_value in http_cookie.split(';'):
            try:
                cookie.load(attr_value)
            except CookieError:
                pass
    cookies = dict([(k, unquote(v.value)) for k, v in cookie.items()])
    return cookies


# lessweb framework exceptions
class NeedParamError(Exception):
    def __init__(self, query, doc):
        self.query: str = query
        self.doc: str = doc

    def __repr__(self):
        return 'lessweb.NeedParamError query:%s doc:%s' % (self.query, self.doc)

    def __str__(self):
        return 'query:%s doc:%s' % (self.query, self.doc)


class BadParamError(Exception):
    def __init__(self, query, error):
        self.query: str = query
        self.error: str = error

    def __repr__(self):
        return 'lessweb.BadParamError query:%s error:%s' % (self.query, self.error)

    def __str__(self):
        return 'query:%s error:%s' % (self.query, self.error)
