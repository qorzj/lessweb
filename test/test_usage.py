from unittest import TestCase
from lessweb.application import Application, interceptor
from lessweb.context import Context
from lessweb.model import need_param


def add1(a, b):
    return {'ans': a + b}


def add2(ctx:Context, a, b):
    return {'ans': ctx.path + ':' + a + b}


def wrapper(ctx:Context):
    value = '[' + ctx()['ans'] + ']'
    return {'ans': value}


@need_param('a', 'b')
def add3(a:int=0, b:int=0):
    return {'ans': a + b}


class TestUsage(TestCase):
    # if argument didn't annotate Context type, then do not inject ctx value
    def test_fetch_param(self):
        app = Application()
        app.add_mapping('/add', 'GET', add1)
        with app.test_get('/add', {'a':'a', 'b':'b'}) as ret:
            self.assertEquals(ret, {'ans': 'ab'})

        app = Application()
        app.add_mapping('/add', 'GET', add2)
        with app.test_get('/add', {'a':'a', 'b':'b'}) as ret:
            self.assertEquals(ret, {'ans': '/add:ab'})

        app = Application()
        app.add_mapping('/add', 'GET', add1)
        app.add_interceptor(wrapper)
        with app.test_get('/add', {'a': 'a', 'b': 'b'}) as ret:
            self.assertEquals(ret, {'ans': '[ab]'})

        app = Application()
        app.add_mapping('/add', 'GET', add2)
        app.add_interceptor(wrapper)
        with app.test_get('/add', {'a': 'a', 'b': 'b'}) as ret:
            self.assertEquals(ret, {'ans': '[/add:ab]'})

        app = Application()
        app.add_mapping('/add', 'GET', interceptor(wrapper)(add1))
        with app.test_get('/add', {'a': 'a', 'b': 'b'}) as ret:
            self.assertEquals(ret, {'ans': '[ab]'})

        app = Application()
        app.add_mapping('/add', 'GET', interceptor(wrapper)(add2))
        with app.test_get('/add', {'a': 'a', 'b': 'b'}) as ret:
            self.assertEquals(ret, {'ans': '[/add:ab]'})

    def test_tips(self):
        app = Application()
        app.add_mapping('/add', 'GET', add3)
        with app.test_get('/add', {'a': 1, 'b': 0}) as ret:
            self.assertEquals(ret, {'ans': 1})