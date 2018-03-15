from unittest import TestCase
from lessweb import Application, interceptor, Context, rest_param


def add1(a, b):
    return {'ans': a + b}


def add2(ctx:Context, a, b):
    return {'ans': ctx.path + ':' + a + b}


def wrapper(ctx:Context):
    value = '[' + ctx()['ans'] + ']'
    return {'ans': value}


def add3(a='x', b='y'):
    return {'ans': a + b}


def wrapper2(ctx:Context):
    ctx.set_param('b', None)
    value = '[' + ctx()['ans'] + ']'
    return {'ans': value}


def wrapper3(ctx:Context):
    return ctx.view.format(ctx()['ans'])


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

    def test_need_param(self):
        app = Application()
        app.add_mapping('/add', 'GET', add3)
        with app.test_get('/add') as ret:
            self.assertEquals(ret, {'ans': 'xy'})

        app = Application()
        app.add_mapping('/add', 'GET', add1)
        with app.test_get('/add', status_code=400) as ret:
            self.assertEquals(ret, 'lessweb.NeedParamError query:a doc:a')

        app = Application()
        f = rest_param('b', default='y')(add1)
        app.add_mapping('/add', 'GET', f)
        with app.test_get('/add', {'a': 'x'}) as ret:
            self.assertEquals(ret, {'ans': 'xy'})

        app = Application()
        f = rest_param('b')(add1)
        app.add_mapping('/add', 'GET', f)
        with app.test_get('/add', {'a': 'x'}, status_code=400) as ret:
            self.assertEquals(ret, 'lessweb.NeedParamError query:b doc:b')

        app = Application()
        app.add_mapping('/add', 'GET', add1)
        with app.test_get('/add', {'a': '1', 'b': '2'}) as ret:
            self.assertEquals(ret, {'ans': '12'})

        app = Application()
        f = rest_param('b', getter=None, default='y')(add3)
        app.add_mapping('/add', 'GET', f)
        with app.test_get('/add', {'a': 1, 'b': 2}) as ret:
            self.assertEquals(ret, {'ans': '1y'})

        app = Application()
        f = rest_param('b', getter=None, default=None)(add1)
        app.add_mapping('/add', 'GET', f)
        with app.test_get('/add', {'a': 1, 'b': 2}, status_code=400) as ret:
            self.assertEquals(ret, 'lessweb.NeedParamError query:b doc:b')

        app = Application()
        app.add_mapping('/add', 'GET', interceptor(wrapper2)(add3))
        with app.test_get('/add', {'a': 2, 'b': 3}) as ret:
            self.assertEquals(ret, {'ans': '[2y]'})

        app = Application()
        app.add_mapping('/add', 'GET', interceptor(wrapper2)(add1))
        with app.test_get('/add', {'a': 2, 'b': 3}, status_code=400) as ret:
            self.assertEquals(ret, 'lessweb.NeedParamError query:b doc:b')

        app = Application()
        app.add_mapping('/add', 'GET', add3)
        with app.test_get('/add', {'a': 2, 'b': 3}) as ret:
            self.assertEquals(ret, {'ans': '23'})

        app = Application()
        app.add_mapping('/add', 'GET', add3, querynames='b')
        with app.test_get('/add', {'a': 2, 'b': 3}) as ret:
            self.assertEquals(ret, {'ans': 'x3'})

        app = Application()
        app.add_mapping('/add', 'GET', add1, querynames='b')
        with app.test_get('/add', {'a': 2, 'b': 3}, status_code=400) as ret:
            self.assertEquals(ret, 'lessweb.NeedParamError query:a doc:a')

    def test_view(self):
        app = Application()
        app.add_mapping('/add', 'GET', interceptor(wrapper3)(add3), view='sum={}')
        with app.test_get('/add') as ret:
            self.assertEquals(ret, 'sum=xy')

    def test_http_error(self):
        app = Application()
        app.add_mapping('/add', 'GET', add1)
        with app.test_get('/add/', {'a': 1, 'b': 2}, status_code=404) as ret:
            self.assertEquals(ret, 'Not Found')

        app = Application()
        app.add_mapping('/add', 'GET', add1)
        with app.test_post('/add', {'a': 1, 'b': 2}, status_code=405) as ret:
            self.assertEquals(ret, 'Method Not Allowed')
