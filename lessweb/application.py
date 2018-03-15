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
from typing import NamedTuple, Any, Callable, Tuple
from enum import Enum
from urllib.parse import splitquery, urlencode
from io import BytesIO
from contextlib import contextmanager

from lessweb.webapi import HttpError, NeedParamError, BadParamError
from lessweb.context import Context
from lessweb.model import fetch_param, Model
from lessweb.storage import Storage
from lessweb.utils import eafp, json_dumps


__all__ = [
    "global_data", "Interceptor", "Mapping", "interceptor", "Application",
]


# Application.interceptors: List[Interceptor]
class Interceptor:
    """Interceptor to定义拦截器based on path prefix"""
    def __init__(self, prefix, method, hook, excludes) -> None:
        self.prefix: str = prefix
        self.method: str = method
        self.hook: Callable = hook
        self.excludes: Tuple = excludes


# Application.mapping: List[Mapping]
class Mapping:
    """Mapping to定义请求处理者和path的对应关系"""
    def __init__(self, pattern, method, hook, doc, patternobj, view, querynames) -> None:
        self.pattern: str = pattern
        self.method: str = method
        self.hook: Callable = hook
        self.doc: str = doc
        self.patternobj: Any = patternobj
        self.view = view
        self.querynames = querynames


def build_controller(hook):
    """
    把接收多个参数的hook转变成只接收一个参数(ctx)的函数

        >>> def controller(ctx, id:int, lpn):
        ...     return {'ctx': ctx, 'id': id, 'lpn': lpn}
        >>> ctx = Context()
        >>> ctx._fields = dict(id='5', lpn='HK888', pageNo='3')
        >>> ret = build_controller(controller)(ctx)
        >>> assert ret == {'ctx': ctx, 'id': 5, 'lpn': 'HK888'}, ret
    """
    def _1_controller(ctx:Context):
        params = fetch_param(ctx, hook)
        return hook(**params)

    return _1_controller


def interceptor(hook):
    """
    为controller添加interceptor的decorator
    hook第一个参数必须是ctx，其他参数的值会从前端请求中获取
    在hook函数中调用ctx()，就会执行它修饰的controller

        >>> def hook(ctx, id:int, pageNo:int):
        ...     assert id == 5 and pageNo == 3, (id, pageNo)
        ...     return list(ctx())
        >>> @interceptor(hook)
        ... def controller(ctx, id:int, lpn):
        ...     return {'ctx': ctx, 'id': id, 'lpn': lpn}
        >>> ctx = Context()
        >>> ctx._fields = dict(id='5', lpn='HK888', pageNo='3')
        >>> ret = build_controller(controller)(ctx)
        >>> assert list(ret) == ['ctx', 'id', 'lpn'], ret
    """
    def _1_wrapper(fn):
        def _1_1_controller(ctx:Context):
            ctx.app_stack.append(build_controller(fn))
            params = fetch_param(ctx, hook)
            result = hook(**params)
            ctx.app_stack.pop()  # 有多次调用ctx()的可能性，比如批量删除
            return result

        return _1_1_controller

    return _1_wrapper


def _make_default_json_encoders():
    def _datetime_encoder(obj:datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')

    def _model_encoder(obj:Model):
        return obj.storage()

    def _enum_encoder(obj:Enum):
        return obj.value

    return [_datetime_encoder, _model_encoder, _enum_encoder]


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
        self.mapping = []
        self.interceptors = []
        self.encoding: str = encoding
        self.debug: bool = debug

    def _load(self, env):
        ctx = Context(self)
        ctx.environ = ctx.env = env
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

    def _handle_with_hooks(self, ctx):
        def _1_mapping_match():
            for mapping in self.mapping:
                _ = mapping.patternobj.search(ctx.path)
                if _ and (mapping.method == ctx.method or mapping.method == '*'):
                    ctx.url_input = _.groupdict()
                    ctx.view = mapping.view
                    if mapping.querynames == '*':
                        ctx.querynames = None
                    elif isinstance(mapping.querynames, str):
                        ctx.querynames = mapping.querynames.replace(',', ' ').split()
                    else:
                        ctx.querynames = mapping.querynames
                    return mapping.hook
            raise HttpError(status_code=404, text='Not Found', headers={})

        try:
            f = build_controller(_1_mapping_match())
            for itr in self.interceptors:
                if ctx.path.startswith(itr.prefix) and (itr.method == ctx.method or itr.method == '*') \
                        and all(not ctx.path.startswith(p) for p in itr.excludes):
                    f = interceptor(itr.hook)(f)
            return f(ctx)
        except HttpError as e:
            return e.text
        except (NeedParamError, BadParamError) as e:
            ctx.status_code = 400
            ctx.reason = 'Bad Request'
            ctx.headers = {'Content-Type': 'text/html'}
            return repr(e)

    def add_interceptor(self, hook, prefix='/', method='*', excludes=('/static/',)):
        """
        Example:

            from lessweb import Application
            app = Application()
            app.add_interceptor(lambda ctx: ctx() + ' world!')
            app.add_mapping('/hello', 'GET', lambda ctx: 'Hello')
            app.run()
        """
        self.interceptors.insert(0, Interceptor(prefix, method, hook, excludes))

    def add_mapping(self, pattern, method, hook, doc='', view=None, querynames='*'):
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
        method = method.upper()
        patternobj = re.compile('^' + pattern + '$')
        self.mapping.append(Mapping(pattern, method, hook, doc, patternobj, view, querynames))

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
                _ = self._handle_with_hooks(ctx)
                result = _1_peep(_) if isinstance(_, GeneratorType) else (_,)
            except Exception as e:
                logging.exception(e)
                ctx.status_code, ctx.reason = 500, 'Internal Server Error'
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
                        ctx.set_header('Content-Type', 'application/json')
                        yield json_dumps(r, _make_default_json_encoders()).encode(self.encoding)

            result = _2_build_result(result)
            status = '{0} {1}'.format(ctx.status_code, ctx.reason)
            ctx.headers.setdefault('Content-Type', 'text/html; charset=' + self.encoding)
            headers = list(ctx.headers.items())
            start_resp(status, headers)
            return itertools.chain(result, (b'',))

        for m in middleware:
            wsgi = m(wsgi)

        return wsgi

    def request(self, localpart='/', method='GET', data=None,
                host="0.0.0.0:8080", headers=None, https=False, env=None):
        path, maybe_query = splitquery(localpart)
        query = maybe_query or ""
        env = env or {}
        env = dict(env, HTTP_HOST=host, REQUEST_METHOD=method, PATH_INFO=path, QUERY_STRING=query, HTTPS=str(https))
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

    def run(self, wsgifunc=None, port:int=8080, homepath=''):
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

        app.router.add_route("*", homepath + "/{path_info:.*}", WSGIHandler(wsgifunc))
        web.run_app(app, port=port)
