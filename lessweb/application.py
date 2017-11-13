"""
Web application
(from salar.py)
"""
from typing import NamedTuple, Any, Callable, Optional, overload, Dict, List, Tuple
import itertools
import json
import os
import re
from types import GeneratorType

from lessweb.webapi import HttpError
from lessweb.sugar import *
from lessweb.context import Context
from lessweb.model import fetch_param
from lessweb.storage import global_data


__all__ = [
    "ModelView", "Interceptor", "Mapping", "Serializer", "interceptor", "Application",
]


class ModelView(NamedTuple):
    """ModelView接口"""
    controller: Callable


# ctx.interceptors: List[Interceptor]
class Interceptor:
    """Interceptor to定义拦截器based on path prefix"""
    def __init__(self, prefix, method, hook, excludes):
        self.prefix: str = prefix
        self.method: str = method
        self.hook: Callable = hook
        self.excludes: Tuple = excludes


# ctx.mapping: List[Mapping]
class Mapping:
    """Mapping to定义请求处理者和path的对应关系"""
    def __init__(self, pattern, method, hook, doc, patternobj):
        self.pattern: str = pattern
        self.method: str = method
        self.hook: Callable = hook
        self.doc: str = doc
        self.patternobj: Any = patternobj


# ctx.serializers: List[Serializer]
class Serializer:
    """为非基础类型指定Serializer"""
    def __init__(self, varclass, func):
        self.varclass: Any = varclass
        self.func: Callable = func


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
    def _1_controller(ctx):
        params = fetch_param(ctx, hook)
        return hook(ctx, **params)

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
        def _1_1_controller(ctx):
            ctx.app_stack.append(build_controller(fn))
            params = fetch_param(ctx, hook)
            result = hook(ctx, **params)
            ctx.app_stack.pop()  # 有多次调用ctx()的可能性，比如批量删除
            return result

        return _1_1_controller

    return _1_wrapper


class Application(object):
    """
    Application to delegate requests based on path.

    Example:

        from salar import Application
        app = Application()
        app.add_mapping('/hello', lambda ctx: 'Hello!')
        app.run(port=8080)

    """
    def __init__(self, encoding='utf-8', debug=True):
        self.mapping = []
        self.interceptors = []
        self.serializers = []
        self.encoding: str = encoding
        self.debug: bool = debug
        global_data.app = self

    def _load(self, env):
        ctx = Context()
        ctx.environ = ctx.env = env
        ctx.host = env.get('HTTP_HOST')
        if env.get('wsgi.url_scheme') in ['http', 'https']:
            ctx.protocol = env['wsgi.url_scheme']
        elif env.get('HTTPS', '').lower() in ['on', 'true', '1']:
            ctx.protocol = 'https'
        else:
            ctx.protocol = 'http'
        ctx.homedomain = ctx.protocol + '://' + env.get('HTTP_HOST', '[unknown]')
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
            e.update(ctx)
            return e.text

    def add_interceptor(self, hook, prefix='/', method='*', excludes=('/static/',)):
        """
        Example:

            from salar import Application
            app = Application()
            app.add_interceptor('/', '*', lambda ctx: ctx() + ' world!')
            app.add_mapping('/hello', lambda ctx: 'Hello')
            app.run()
        """
        self.interceptors.insert(0, Interceptor(prefix, method, hook, excludes))

    def add_mapping(self, pattern, method, hook, doc=''):
        """
        Example:

            from salar import Application
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
        if _is(ModelView)(hook):
            hook = hook.controller
        self.mapping.append(Mapping(pattern, method, hook, doc, patternobj))

    def add_serializer(self, varclass, func):
        """
        Example:

            from datetime import datetime
            from salar import Application
            app = Application()
            app.add_serializer(varclass=datetime, func=lambda x: x.strftime('%H:%M:%S'))
            app.add_mapping('/now', 'GET', lambda ctx: {'time': datetime.now()})
            app.run()
        """
        assert isinstance(varclass, type) or \
               (isinstance(varclass, tuple) and all(isinstance(x, type) for x in varclass)), \
            str(varclass)
        self.serializers.append(Serializer(varclass, func))

    def serialize(self, obj)->str:
        """
        把obj序列化为str

            >>> from datetime import datetime
            >>> app = Application(encoding='utf-8')
            >>> app.add_serializer(varclass=datetime, func=lambda x: x.strftime('%Y-%m-%d'))
            >>> app.serialize({'time': datetime(2000, 1, 1)})
            '{"time": "2000-01-01"}'
        """
        serializers = self.serializers
        class _1_Encoder(json.JSONEncoder):
            def default(self, obj):
                for f in serializers:
                    if isinstance(obj, f.varclass):
                        return f.func(obj)
                return json.JSONEncoder.default(self, obj)

        return json.dumps(obj, cls=_1_Encoder)

    def wsgifunc(self, *middleware):
        """
            Example:

                import salar
                app = salar.Application()
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
                import logging
                logging.exception(e)
                ctx.status_code, ctx.reason = 500, 'Internal Server Error'
                result = (str(e),)

            def _2_build_result(result):
                for r in result:
                    if isinstance(r, bytes):
                        yield r
                    elif isinstance(r, str):
                        yield r.encode(self.encoding)
                    elif r is None:
                        yield b''
                    else:
                        yield self.serialize(r).encode(self.encoding)

            result = _2_build_result(result)
            status = '{0} {1}'.format(ctx.status_code, ctx.reason)
            ctx.headers.setdefault('Content-Type', 'text/html')
            headers = list(ctx.headers.items())
            start_resp(status, headers)
            return itertools.chain(result, (b'',))

        for m in middleware:
            wsgi = m(wsgi)

        return wsgi

    def run(self, wsgifunc=None, port: int=8080):
        """
        Example:

            from salar import Application
            app = Application()
            app.add_interceptor('/', '*', lambda ctx: ctx() + ' world!')
            app.add_mapping('/hello', lambda ctx: 'Hello')
            app.run(port=80)
        """
        from aiohttp import web
        from aiohttp_wsgi import WSGIHandler
        app = web.Application()
        if wsgifunc is None:
            wsgifunc = self.wsgifunc()
        app.router.add_route("*", "/{path_info:.*}", WSGIHandler(wsgifunc))
        web.run_app(app, port=port)
