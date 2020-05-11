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
from typing import List, Any, Callable, Dict, Optional

from .webapi import BadParamError, NotFoundError, HttpStatus
from .webapi import http_methods
from .context import Context
from .model import fetch_param
from .storage import Storage
from .utils import eafp, re_standardize, makedir
from .bridge import make_response_encoder, JsonBridgeFunc
from .pluginproto import PluginProto


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
    def __init__(self, pattern, method, dealer, doc, patternobj) -> None:
        self.pattern: str = pattern
        self.method: str = method
        self.dealer: Callable = dealer
        self.doc: str = doc
        self.patternobj: Any = patternobj


def build_controller(dealer):
    """
    把接收多个参数的dealer转变成只接收一个参数(ctx)的函数
    """
    def _1_controller(ctx:Context):
        try:
            args, params = fetch_param(ctx, dealer)
        except BadParamError:
            raise
        except Exception as e:
            raise BadParamError(message=str(e), param='')
        return dealer(*args, **params)

    return _1_controller


def interceptor(dealer):
    """
    为controller添加interceptor的decorator
    在dealer函数中调用ctx()，就会执行它修饰的controller
    """
    def _1_wrapper(fn):
        def _1_1_controller(ctx:Context):
            ctx.app_stack.append(build_controller(fn))
            args, params = fetch_param(ctx, dealer)
            result = dealer(*args, **params)
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
    def __init__(self, encoding:str='utf-8') -> None:
        self.mapping: List[Mapping] = []
        self.interceptors: List[Interceptor] = []
        self.response_bridges: List[Callable] = []
        self.response_encoder: Any = make_response_encoder([])
        self.encoding: str = encoding
        self.plugins: List[PluginProto] = []

    def _handle_with_dealers(self, ctx: Context):
        def _1_mapping_match():
            supported_methods = []
            for mapping in self.mapping:
                _ = mapping.patternobj.search(ctx.request.path)
                if _:
                    if mapping.method == ctx.request.method or mapping.method == '*':
                        ctx.request.param_input.load_url(_.groupdict())
                        return mapping.dealer
                    elif mapping.method != 'OPTIONS':
                        supported_methods.append(mapping.method)
            # end: for
            raise NotFoundError(methods=supported_methods)

        try:
            f = build_controller(_1_mapping_match())
            if f is None: return ''
            for itr in self.interceptors:
                if itr.patternobj.search(ctx.request.path) and (itr.method == ctx.request.method or itr.method == '*'):
                    f = interceptor(itr.dealer)(f)
            return f(ctx)
        except BadParamError as e:
            ctx.response.set_status(HttpStatus.BadRequest)
            return {'message': e.message, 'param': e.param}
        except NotFoundError as e:
            if e.methods:
                ctx.response.send_allow_methods(e.methods)
                ctx.response.set_status(HttpStatus.MethodNotAllowed)
            else:
                ctx.response.set_status(HttpStatus.NotFound)
            return repr(e)

    def add_interceptor(self, pattern: str, method: str, dealer: Callable):
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
        assert method == '*' or method in http_methods, 'Method:[{}] should be * or one of {}'.format(method, http_methods)
        patternobj = re.compile(re_standardize(pattern))
        self.interceptors.insert(0, Interceptor(pattern, method, dealer, patternobj))

    def add_json_bridge(self, bridge_func: JsonBridgeFunc):
        self.response_bridges.append(bridge_func)
        self.response_encoder = make_response_encoder(self.response_bridges)

    def add_mapping(self, pattern: str, method: str, dealer: Callable):
        """
        Example:

            from lessweb import Application
            def say_hello(ctx, name):
                return 'Hello %s!' % name
            app = Application()
            app.add_mapping('/hello/(?P<name>.+)', 'GET', say_hello)
            app.run()
        """
        assert isinstance(pattern, str), 'pattern:[{}] should be RegExp str'.format(pattern)
        method = method.upper()
        assert method == '*' or method in http_methods, 'Method:[{}] should be * or one of {}'.format(method, http_methods)
        patternobj = re.compile(re_standardize(pattern))
        self.mapping.append(Mapping(pattern, method, dealer, '', patternobj))

    # add_*_interceptor / add_*_mapping are generated by code below:
    """
    for m in ['CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT']:
        print(("def add_{m}_interceptor(self, pattern, dealer): return self.add_interceptor(pattern, '{M}', dealer)\n"
        "def add_{m}_mapping(self, pattern, dealer, view=None): return self.add_mapping(pattern, '{M}', dealer, view)\n")
        .format(m=m.lower(), M=m))
    """
    def add_connect_interceptor(self, pattern: str, dealer: Callable):
        return self.add_interceptor(pattern, 'CONNECT', dealer)

    def add_connect_mapping(self, pattern: str, dealer: Callable):
        return self.add_mapping(pattern, 'CONNECT', dealer)

    def add_delete_interceptor(self, pattern: str, dealer: Callable):
        return self.add_interceptor(pattern, 'DELETE', dealer)

    def add_delete_mapping(self, pattern: str, dealer: Callable):
        return self.add_mapping(pattern, 'DELETE', dealer)

    def add_get_interceptor(self, pattern: str, dealer: Callable):
        return self.add_interceptor(pattern, 'GET', dealer)

    def add_get_mapping(self, pattern: str, dealer: Callable):
        return self.add_mapping(pattern, 'GET', dealer)

    def add_head_interceptor(self, pattern: str, dealer: Callable):
        return self.add_interceptor(pattern, 'HEAD', dealer)

    def add_head_mapping(self, pattern: str, dealer: Callable):
        return self.add_mapping(pattern, 'HEAD', dealer)

    def add_options_interceptor(self, pattern: str, dealer: Callable):
        return self.add_interceptor(pattern, 'OPTIONS', dealer)

    def add_options_mapping(self, pattern: str, dealer: Callable):
        return self.add_mapping(pattern, 'OPTIONS', dealer)

    def add_patch_interceptor(self, pattern: str, dealer: Callable):
        return self.add_interceptor(pattern, 'PATCH', dealer)

    def add_patch_mapping(self, pattern: str, dealer: Callable):
        return self.add_mapping(pattern, 'PATCH', dealer)

    def add_post_interceptor(self, pattern: str, dealer: Callable):
        return self.add_interceptor(pattern, 'POST', dealer)

    def add_post_mapping(self, pattern: str, dealer: Callable):
        return self.add_mapping(pattern, 'POST', dealer)

    def add_put_interceptor(self, pattern: str, dealer: Callable):
        return self.add_interceptor(pattern, 'PUT', dealer)

    def add_put_mapping(self, pattern: str, dealer: Callable):
        return self.add_mapping(pattern, 'PUT', dealer)

    def add_plugin(self, plugin: PluginProto):
        self.plugins.append(plugin)
        plugin.init_app(self)

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

            ctx = Context(self)
            ctx.request.load(env)
            try:
                mimekey = 'html'
                resp = self._handle_with_dealers(ctx)
                resp_content_type = ctx.response.get_header('Content-Type')
                if isinstance(resp, GeneratorType):
                    result = _1_peep(resp)
                else:
                    if not isinstance(resp, (bytes, str)) and resp is not None:
                        if not resp_content_type or \
                                (resp_content_type and 'json' in resp_content_type.lower()):
                            resp = json.dumps(resp, ensure_ascii=False, cls=self.response_encoder)
                            mimekey = 'json'
                        else:
                            resp = str(resp)
                    result = (resp,)
                if not resp_content_type:
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
                        yield r.encode(self.encoding, 'replace')
                    elif r is None:
                        yield b''
                    else:
                        yield str(r).encode(self.encoding)

            result = _2_build_result(result)
            status_wrap = ctx.response.get_status()
            status_core = status_wrap.value if isinstance(status_wrap, HttpStatus) else status_wrap
            status_text = f'{status_core.code} {status_core.reason}'
            headers = list(ctx.response._headers.items())
            for cookie in ctx.response._cookies.values():
                headers.append(('Set-Cookie', cookie.dumps()))
            start_resp(status_text, headers)
            return itertools.chain(result, (b'',))

        for m in middleware:
            wsgi = m(wsgi)

        return wsgi

    def run(self, wsgifunc=None, port:int=8080, homepath:str='', staticpath:Optional[str]='static'):
        """
        Example:

            from lessweb import Application
            app = Application()
            app.add_interceptor('/', '*', lambda ctx: ctx() + ' world!')
            app.add_mapping('/hello', lambda ctx: 'Hello')
            app.run(port=80, homepath='/api')
        """
        from aiohttp import web
        from aiohttp_wsgi import WSGIHandler  # type: ignore
        app = web.Application()
        if wsgifunc is None:
            wsgifunc = self.wsgifunc()

        if homepath.endswith('/'):
            homepath = homepath[:-1]
        if homepath and homepath[0] != '/':
            homepath = '/' + homepath

        if staticpath is not None:
            makedir(staticpath)
            app.router.add_static(prefix='/static/', path=staticpath)
        app.router.add_route("*", homepath + "/{path_info:.*}", WSGIHandler(wsgifunc))
        web.run_app(app, port=port)
