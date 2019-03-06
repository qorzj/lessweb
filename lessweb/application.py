"""
Web application
(from lessweb)
"""
from datetime import datetime
import itertools
import json
import logging
import os
import re
import traceback
from types import GeneratorType
from typing import List, Any, Callable, Type
from urllib.parse import splitquery, urlencode
from io import BytesIO
from contextlib import contextmanager

from lessweb.webapi import NeedParamError, BadParamError, NotFoundError, HttpStatus
from lessweb.webapi import http_methods
from lessweb.context import Context
from lessweb.model import fetch_param, ModelToDict
from lessweb.storage import Storage
from lessweb.utils import eafp, re_standardize, makedir
from lessweb.bridge import Bridge, assert_valid_bridge
from lessweb.garage import Jsonizable, BaseBridge, JsonToJson


__all__ = [
    "Interceptor", "Mapping", "interceptor", "Application",
]


# Application.interceptors: List[Interceptor]
class Interceptor:
    """Interceptor to定义拦截器based on path prefix"""
    def __init__(self, pattern, method, dealer, patternobj) -> None:
        self.pattern: str = pattern
        self.method: str = method
        self.dealer: Callable = dealer
        self.patternobj: Any = patternobj


# Application.mapping: List[Mapping]
class Mapping:
    """Mapping to定义请求处理者和path的对应关系"""
    def __init__(self, pattern, method, dealer, doc, patternobj, view, querynames) -> None:
        self.pattern: str = pattern
        self.method: str = method
        self.dealer: Callable = dealer
        self.doc: str = doc
        self.patternobj: Any = patternobj
        self.view = view
        self.querynames = querynames


def build_controller(dealer):
    """
    把接收多个参数的dealer转变成只接收一个参数(ctx)的函数

        >>> def controller(ctx:Context, id:int, lpn):
        ...     return {'ctx': ctx, 'id': id, 'lpn': lpn}
        >>> ctx = Context()
        >>> ctx._fields = dict(id='5', lpn='HK888', pageNo='3')
        >>> ret = build_controller(controller)(ctx)
        >>> assert ret == {'ctx': ctx, 'id': 5, 'lpn': 'HK888'}, ret
    """
    def _1_controller(ctx:Context):
        params = fetch_param(ctx, dealer)
        return dealer(**params)

    return _1_controller


def interceptor(dealer):
    """
    为controller添加interceptor的decorator
    在dealer函数中调用ctx()，就会执行它修饰的controller

        >>> def dealer(ctx:Context, id:int, pageNo:int):
        ...     assert id == 5 and pageNo == 3, (id, pageNo)
        ...     return list(ctx())
        >>> @interceptor(dealer)
        ... def controller(ctx:Context, id:int, lpn):
        ...     return {'ctx': ctx, 'id': id, 'lpn': lpn}
        >>> ctx = Context()
        >>> ctx._fields = dict(id='5', lpn='HK888', pageNo='3')
        >>> ret = build_controller(controller)(ctx)
        >>> assert list(ret) == ['ctx', 'id', 'lpn'], ret
    """
    def _1_wrapper(fn):
        def _1_1_controller(ctx:Context):
            ctx.app_stack.append(build_controller(fn))
            params = fetch_param(ctx, dealer)
            result = dealer(**params)
            ctx.app_stack.pop()  # 有多次调用ctx()的可能性，比如批量删除
            return result

        return _1_1_controller

    return _1_wrapper


class Application(object):
    """
    Application to delegate requests based on path.

    Example:

        from lessweb import Application
        app = Application()
        app.add_mapping('/hello', lambda ctx: 'Hello!')
        app.run(port=8080)

    """
    def __init__(self, encoding='utf-8', debug=True) -> None:
        self.mapping: List[Mapping] = []
        self.interceptors: List[Interceptor] = []
        self.bridges: List[Bridge] = [JsonToJson, ModelToDict]
        self.encoding: str = encoding
        self.debug: bool = debug

    def _load(self, env):
        ctx = Context(self)
        ctx.request.env = ctx.environ = ctx.env = env
        ctx.host = env.get('HTTP_HOST', '[unknown]')
        if env.get('wsgi.url_scheme') in ['http', 'https']:
            ctx.protocol = env['wsgi.url_scheme']
        elif env.get('HTTPS', '').lower() in ['on', 'true', '1']:
            ctx.protocol = 'https'
        else:
            ctx.protocol = 'http'
        ctx.homedomain = ctx.protocol + '://' + ctx.host
        ctx.homepath = os.environ.get('REAL_SCRIPT_NAME', env.get('SCRIPT_NAME', ''))
        ctx.home = ctx.homedomain + ctx.homepath
        # @@ home is changed when the request is handled to a sub-application.
        # @@ but the real home is required for doing absolute redirects.
        ctx.realhome = ctx.home
        ctx.ip = env.get('REMOTE_ADDR')
        ctx.method = env.get('REQUEST_METHOD')
        ctx.path = env.get('PATH_INFO')
        # http://trac.lighttpd.net/trac/ticket/406 requires:
        if env.get('SERVER_SOFTWARE', '').startswith('lighttpd/'):
            ctx.path = env.get('REQUEST_URI').split('?')[0][:len(ctx.homepath)]
            # unquote explicitly for lighttpd to make ctx.path uniform across all servers.
            from urllib.parse import unquote
            ctx.path = unquote(ctx.path)

        ctx.query = env.get('QUERY_STRING')
        ctx.fullpath = ctx.path + '?' + ctx.query if ctx.query else ctx.path
        return ctx

    def _handle_with_dealers(self, ctx):
        def _1_mapping_match():
            supported_methods = []
            for mapping in self.mapping:
                _ = mapping.patternobj.search(ctx.path)
                if _:
                    if mapping.method == ctx.method or mapping.method == '*':
                        ctx._url_input.update(_.groupdict())
                        ctx.view = mapping.view
                        if mapping.querynames == '*':
                            ctx.querynames = None
                        elif isinstance(mapping.querynames, str):
                            ctx.querynames = mapping.querynames.replace(',', ' ').split()
                        else:
                            ctx.querynames = mapping.querynames
                        return mapping.dealer
                    elif mapping.method != 'OPTIONS':
                        supported_methods.append(mapping.method)
            # end: for
            raise NotFoundError(methods=supported_methods)

        try:
            f = build_controller(_1_mapping_match())
            if f is None: return ''
            for itr in self.interceptors:
                if itr.patternobj.search(ctx.path) and (itr.method == ctx.method or itr.method == '*'):
                    f = interceptor(itr.dealer)(f)
            return f(ctx)
        except (NeedParamError, BadParamError) as e:
            ctx.response.set_status(HttpStatus.BadRequest)
            return repr(e)
        except NotFoundError as e:
            if e.methods:
                ctx.response.send_allow_methods(e.methods)
                ctx.response.set_status(HttpStatus.MethodNotAllowed)
            else:
                ctx.response.set_status(HttpStatus.NotFound)
            return repr(e)

    def add_interceptor(self, pattern, method, dealer):
        """
        Example:

            from lessweb import Application
            app = Application()
            app.add_interceptor(lambda ctx: ctx() + ' world!')
            app.add_mapping('/hello', 'GET', lambda ctx: 'Hello')
            app.run()
        """
        assert isinstance(pattern, str), 'pattern:[{}] should be RegExp str'.format(pattern)
        method = method.upper()
        assert method == '*' or method in http_methods, 'Method:[{}] should be one of {}'.format(method, ['*'] + http_methods)
        patternobj = re.compile(re_standardize(pattern))
        self.interceptors.insert(0, Interceptor(pattern, method, dealer, patternobj))

    def add_bridge(self, bridge: Type[Bridge]):
        assert_valid_bridge(bridge)
        self.bridges.append(bridge)

    def add_mapping(self, pattern, method, dealer, view=None):
        """
        Example:

            from lessweb import Application
            def sayhello(ctx, name):
                return 'Hello %s!' % name
            def sayage(ctx, age: int, name='Bob'):
                return 'Name: %s, Age: %d' % (name, age)
            app = Application()
            app.add_mapping('/hello/(?P<name>.+)', 'GET', sayhello)
            app.add_mapping('/age/(?P<age>[0-9]+)', 'GET', sayhello)
            app.run()
        """
        assert isinstance(pattern, str), 'pattern:[{}] should be RegExp str'.format(pattern)
        method = method.upper()
        assert method == '*' or method in http_methods, 'Method:[{}] should be one of {}'.format(method, ['*'] + http_methods)
        patternobj = re.compile(re_standardize(pattern))
        self.mapping.append(Mapping(pattern, method, dealer, '', patternobj, view, '*'))

    # add_*_interceptor / add_*_mapping are generated by code below:
    """
    for m in ['CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT']:
        print(("def add_{m}_interceptor(self, pattern, dealer): return self.add_interceptor(pattern, '{M}', dealer)\n"
        "def add_{m}_mapping(self, pattern, dealer, view=None): return self.add_mapping(pattern, '{M}', dealer, view)\n")
        .format(m=m.lower(), M=m))
    """
    def add_connect_interceptor(self, pattern, dealer):
        return self.add_interceptor(pattern, 'CONNECT', dealer)

    def add_connect_mapping(self, pattern, dealer, view=None):
        return self.add_mapping(pattern, 'CONNECT', dealer, view)

    def add_delete_interceptor(self, pattern, dealer):
        return self.add_interceptor(pattern, 'DELETE', dealer)

    def add_delete_mapping(self, pattern, dealer, view=None):
        return self.add_mapping(pattern, 'DELETE', dealer, view)

    def add_get_interceptor(self, pattern, dealer):
        return self.add_interceptor(pattern, 'GET', dealer)

    def add_get_mapping(self, pattern, dealer, view=None):
        return self.add_mapping(pattern, 'GET', dealer, view)

    def add_head_interceptor(self, pattern, dealer):
        return self.add_interceptor(pattern, 'HEAD', dealer)

    def add_head_mapping(self, pattern, dealer, view=None):
        return self.add_mapping(pattern, 'HEAD', dealer, view)

    def add_options_interceptor(self, pattern, dealer):
        return self.add_interceptor(pattern, 'OPTIONS', dealer)

    def add_options_mapping(self, pattern, dealer, view=None):
        return self.add_mapping(pattern, 'OPTIONS', dealer, view)

    def add_post_interceptor(self, pattern, dealer):
        return self.add_interceptor(pattern, 'POST', dealer)

    def add_post_mapping(self, pattern, dealer, view=None):
        return self.add_mapping(pattern, 'POST', dealer, view)

    def add_put_interceptor(self, pattern, dealer):
        return self.add_interceptor(pattern, 'PUT', dealer)

    def add_put_mapping(self, pattern, dealer, view=None):
        return self.add_mapping(pattern, 'PUT', dealer, view)

    def wsgifunc(self, *middleware):
        """
            Example:

                import lessweb
                app = lessweb.Application()
                app.add_interceptor('/', '*', lambda ctx: ctx() + ' world!')
                app.add_mapping('/hello', lambda ctx: 'Hello')
                application = app.wsgifunc()
        """
        def wsgi(env, start_resp):
            def _1_peep(iterator):
                """Peeps into an iterator by doing an iteration
                and returns an equivalent iterator.
                """
                # wsgi requires the headers first
                # so we need to do an iteration
                # and save the result for later
                try:
                    firstchunk = next(iterator)
                except StopIteration:
                    firstchunk = ''
                return itertools.chain([firstchunk], iterator)

            ctx = self._load(env)
            try:
                mimekey = 'html'
                resp = self._handle_with_dealers(ctx)
                if isinstance(resp, GeneratorType):
                    result = _1_peep(resp)
                else:
                    if not isinstance(resp, (bytes, str)) and resp is not None:
                        baseBridge = BaseBridge()
                        baseBridge.init_for_cast(self.bridges)
                        resp = json.dumps(baseBridge.cast(resp, type(resp), Jsonizable))
                        mimekey = 'json'
                    result = (resp,)
                if not ctx.response.get_header('Content-Type'):
                    ctx.response.send_content_type(mimekey=mimekey, encoding=self.encoding)
            except Exception as e:
                logging.exception(e)
                ctx.response.send_content_type(encoding=self.encoding)
                ctx.response.set_status(HttpStatus.InternalServerError)
                result = (traceback.format_exc(),)

            def _2_build_result(result):
                for r in result:
                    if isinstance(r, bytes):
                        yield r
                    elif isinstance(r, str):
                        yield r.encode(self.encoding)
                    elif r is None:
                        yield b''
                    else:
                        yield str(r).encode(self.encoding)

            result = _2_build_result(result)
            status = ctx.response.get_status().value
            status_text = '{0} {1}'.format(status.code, status.reason)
            headers = list(ctx.response._headers.items())
            for cookie in ctx.response._cookies.values():
                headers.append(('Set-Cookie', cookie.dumps()))
            start_resp(status_text, headers)
            return itertools.chain(result, (b'',))

        for m in middleware:
            wsgi = m(wsgi)

        return wsgi

    def request(self, localpart='/', method='GET', data=None,
                host="0.0.0.0:8080", headers=None, https=False, env=None):
        path, maybe_query = splitquery(localpart)
        query = maybe_query or ""
        env = env or {}
        env = dict(env, HTTP_HOST=host, REMOTE_ADDR='127.0.0.1', REQUEST_METHOD=method, PATH_INFO=path, QUERY_STRING=query, HTTPS=str(https))
        headers = headers or {}

        for k, v in headers.items():
            env['HTTP_' + k.upper().replace('-', '_')] = v

        if 'HTTP_CONTENT_LENGTH' in env:
            env['CONTENT_LENGTH'] = env.pop('HTTP_CONTENT_LENGTH')

        if 'HTTP_CONTENT_TYPE' in env:
            env['CONTENT_TYPE'] = env.pop('HTTP_CONTENT_TYPE')

        if method not in ["HEAD", "GET", "DELETE"]:
            data = data or ''
            if isinstance(data, dict):
                q = urlencode(data)
            else:
                q = data
            env['wsgi.input'] = BytesIO(q.encode('utf-8'))
            if 'CONTENT_LENGTH' not in env:
                # if not env.get('CONTENT_TYPE', '').lower().startswith('multipart/') and 'CONTENT_LENGTH' not in env:
                env['CONTENT_LENGTH'] = len(q)

        response = Storage()

        def start_response(status, headers):
            response.status = status
            response.status_code = int(status.split()[0])
            response.headers = dict(headers)
            response.header_items = headers

        data = self.wsgifunc()(env, start_response)
        response.data = b"".join(data)
        return response

    @contextmanager
    def _reqtest(self, localpart='/', method='GET', data=None, headers=None, status_code=200, parsejson=True, https=False, env=None):
        response_obj = ()
        try:
            ret = self.request(localpart=localpart, method=method, data=data, headers=headers, https=https, env=env)
            ret.text = ret.data.decode(self.encoding)
            if parsejson:
                response_obj = eafp(lambda : json.loads(ret.text), ret.text)
            else:
                response_obj = ret.text
            assert ret.status_code == status_code, 'status_code: {}\ntext: {}\n'.format(ret.status_code, ret.text)
            yield response_obj
        except Exception as e:
            logging.exception(e)
            logging.fatal('req-url: %s\n' % localpart)
            logging.fatal('req-data: %s\n' % json.dumps(data))
            logging.fatal('req-headers: %s\n' % json.dumps(headers))
            if response_obj != ():
                logging.fatal('response: %s\n' % response_obj)
            raise

    def test_get(self, localpart='/', query=None, headers=None, status_code=200, parsejson=True, https=False, env=None):
        if query:
            localpart = localpart + '?' + urlencode(query)
        return self._reqtest(localpart, 'GET', None, headers, status_code, parsejson, https, env)

    def test_delete(self, localpart='/', query=None, headers=None, status_code=200, parsejson=True, https=False, env=None):
        if query:
            localpart = localpart + '?' + urlencode(query)
        return self._reqtest(localpart, 'DELETE', None, headers, status_code, parsejson, https, env)

    def test_head(self, localpart='/', query=None, headers=None, status_code=200, parsejson=True, https=False, env=None):
        if query:
            localpart = localpart + '?' + urlencode(query)
        return self._reqtest(localpart, 'HEAD', None, headers, status_code, parsejson, https, env)

    def test_post(self, localpart='/', data=None, headers=None, status_code=200, parsejson=True, https=False, env=None):
        return self._reqtest(localpart, 'POST', data, headers, status_code, parsejson, https, env)

    def test_put(self, localpart='/', data=None, headers=None, status_code=200, parsejson=True, https=False, env=None):
        return self._reqtest(localpart, 'PUT', data, headers, status_code, parsejson, https, env)

    def run(self, wsgifunc=None, port:int=8080, homepath='', staticpath='static'):
        """
        Example:

            from lessweb import Application
            app = Application()
            app.add_interceptor('/', '*', lambda ctx: ctx() + ' world!')
            app.add_mapping('/hello', lambda ctx: 'Hello')
            app.run(port=80, homepath='/api')
        """
        from aiohttp import web
        from aiohttp_wsgi import WSGIHandler
        app = web.Application()
        if wsgifunc is None:
            wsgifunc = self.wsgifunc()

        if homepath.endswith('/'):
            homepath = homepath[:-1]
        if homepath and homepath[0] != '/':
            homepath = '/' + homepath

        if staticpath is not None:
            makedir('static')
            app.router.add_static(prefix='/static/', path=staticpath)
        app.router.add_route("*", homepath + "/{path_info:.*}", WSGIHandler(wsgifunc))
        web.run_app(app, port=port)
