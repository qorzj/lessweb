from unittest import TestCase
from lessweb.application import Application, interceptor
from lessweb.context import Context


def add(ctx:Context, a, b):
    ctx.status_code, ctx.reason = 204, 'No Content'
    return a + b


def wrapper(ctx:Context):
    return '[{}]'.format(ctx())


class TestWebapi(TestCase):
    def test_200s(self):
        app = Application()
        app.add_mapping('/add', 'GET', add)
        app.add_interceptor('/add', 'GET', add)
        ret = app.request('/add?a=1&b=2')
        self.assertEquals(ret.status, '204 No Content')