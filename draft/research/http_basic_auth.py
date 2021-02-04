from typing import Iterable, Dict
import base64
import re
from lessweb import Application, Context, HttpStatus


class BaseAuthPlugin:
    passwords: Dict[str, str]
    patterns: Iterable[str]

    def __init__(self, passwords: Dict[str, str], patterns: Iterable[str]=('.*',)):
        self.passwords = passwords
        self.patterns = patterns

    def init_app(self, app: Application) -> None:
        for pattern in self.patterns:
            app.add_interceptor(pattern, method='*', dealer=self.admin_authorise)

    def teardown(self, exception: Exception):
        pass

    def auth_is_allowed(self, ctx: Context) -> bool:
        auth = ctx.request.env.get('HTTP_AUTHORIZATION')
        if auth is None: return False
        auth = re.sub('^Basic ', '', auth).encode()
        username, password = base64.decodebytes(auth).decode().split(':')
        return self.passwords.get(username) == password

    def admin_authorise(self, ctx: Context):
        if not self.auth_is_allowed(ctx):
            ctx.response.set_header('WWW-Authenticate', 'Basic realm="Auth Example"')
            ctx.response.set_status(HttpStatus.Unauthorized)
        return ctx()
