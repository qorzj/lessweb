from unittest import TestCase
from lessweb import Application, Response, HttpStatus, UploadedFile, Context, interceptor


class TestWiki(TestCase):
    def test_hello_world(self):
        def hello():
            return 'Hello, world!'
        app = Application()
        app.add_get_mapping('/', hello)
        with app.test_get('/', parsejson=False) as ret:
            self.assertEqual('Hello, world!', ret)

    def test_simple_request(self):
        def f(x: int, y: int = 100):
            return {'sum': x + y}
        app = Application()
        app.add_get_mapping('/ad*', dealer=f)
        with app.test_get('/addd?x=3&y=4') as ret:
            self.assertEqual({"sum": 7}, ret)
        with app.test_get('/a?x=3') as ret:
            self.assertEqual({"sum": 103}, ret)
        with app.test_get('/add', status_code=400, parsejson=False) as ret:
            self.assertEqual('lessweb.NeedParamError query:x doc:x', ret)
        with app.test_get('/addd?x=1&y=x', status_code=400, parsejson=False) as ret:
            self.assertEqual("lessweb.BadParamError query:y error:invalid literal for int() with base 10: 'x'", ret)

    def test_path_variable(self):
        def book_detail(bookId: int, author: str):
            return {'bookId': bookId, 'author': author}
        app = Application()
        app.add_get_mapping('/book/{bookId}', dealer=book_detail)
        with app.test_get('/book/1357?author=None') as ret:
            self.assertEqual({"bookId": 1357, "author": "None"}, ret)

    def test_redirect(self):
        def f(): return 'Hello'
        def g(resp: Response):
            resp.send_redirect('/home/a')
            resp.set_status(HttpStatus.SeeOther)
            return ''
        app = Application()
        app.add_get_mapping('/a', dealer=f)
        app.add_get_mapping('/b', dealer=g)
        with app.test_get('/b', status_code=303, parsejson=False) as ret:
            self.assertEqual(ret, '')

    def test_upload_file(self):
        def upload(f: UploadedFile, id: int):
            summary = f.value[:10] + b'...'
            return {'id': id, 'filename': f.filename, 'value': summary.decode(), 'size': len(f.value)}
        app = Application()
        app.add_post_mapping('/upload', dealer=upload)
        with app.test_post('/upload', {'id': 6, 'f': '@'}, status_code=400, parsejson=False) as ret:
            self.assertEqual(ret, 'lessweb.BadParamError query:f error:Uploaded File Only')

    def test_context(self):
        def info(ctx: Context, msg):
            return {'msg': msg, 'ip': ctx.ip}
        app = Application()
        app.add_get_mapping('/info', dealer=info)
        with app.test_get('/info?msg=lol') as ret:
            self.assertEqual(ret, {"msg": "lol", "ip": "127.0.0.1"})

    def test_rawdata(self):
        def raw(ctx: Context):
            return {'method': ctx.method, 'data': ctx.body_data().decode()}
        app = Application()
        app.add_mapping('/data', method='*', dealer=raw)
        with app.test_post('/data', data='<xml>123</xml>') as ret:
            self.assertEqual(ret, {"method": "POST", "data": "<xml>123</xml>"})

    def test_cookie(self):
        def set_user(ctx: Context, name):
            ctx.response.set_cookie('username', name)
            return 'ok'

        def get_user(ctx: Context):
            username = ctx.request.get_cookie('username')
            return {'user': username}

        app = Application()
        app.add_post_mapping('/set', dealer=set_user)
        app.add_get_mapping('/get', dealer=get_user)
        ret = app.request('/set', method='POST', data={'name': 'John'})
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b'ok')
        self.assertEqual(ret.headers, {'Content-Type': 'text/html; charset=utf-8', 'Set-Cookie': 'username=John; Path=/'})
        ret = app.request('/get', headers={'Cookie': 'username=John'})
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b'{"user": "John"}')

    def test_interceptor(self):
        def hookA(ctx: Context):
            return '[%s]' % ctx()

        def hookB(ctx: Context, a):
            assert a == 'A'
            return '(%s)' % ctx()

        def controller(a):
            return a

        app = Application()
        app.add_get_interceptor('.*', dealer=hookA)
        app.add_get_interceptor('.*', dealer=hookB)
        app.add_get_mapping('/info', dealer=controller)
        with app.test_get('/info?a=A', parsejson=False) as ret:
            self.assertEqual(ret, '[(A)]')

        def hookA(ctx: Context):
            return '[%s]' % ctx()

        def hookB(ctx: Context, a):
            assert a == 'B'
            return '<%s>' % ctx()

        @interceptor(hookA)
        @interceptor(hookB)
        def controller(a):
            return a

        app = Application()
        app.add_get_mapping('/info', dealer=controller)
        with app.test_get('/info?a=B', parsejson=False) as ret:
            self.assertEqual(ret, '[<B>]')

    def test_alias(self):
        def rename(ctx: Context):
            ctx.set_alias('try_', 'try')
            return ctx()

        @interceptor(rename)
        def controller(try_: int):
            return {'try': try_}

        app = Application()
        app.add_get_mapping('/alias', dealer=controller)
        with app.test_get('/alias?try=5') as ret:
            self.assertEqual(ret, {"try": 5})

        def rename(ctx: Context):
            ret = []
            ctx.set_alias('try_', 'try')
            ret.append(ctx())
            ctx.set_param('try_', 'N')
            ret.append(ctx())
            return ret

        @interceptor(rename)
        def controller(ctx: Context, try_: int):
            return {'try': try_, '*': ctx.get_param('try_', 0)}

        app = Application()
        app.add_get_mapping('/alias', dealer=controller)
        with app.test_get('/alias?try=5') as ret:
            self.assertEqual(ret, [{"try": 5, "*": 0}, {"try": 5, "*": "N"}])

    def test_view(self):
        def homepage(data):
            return '<%s/>' % data['who']

        def show_view(ctx: Context):
            data = ctx()
            return ctx.view(data)

        def home(who):
            return {'who': who}

        app = Application()
        app.add_get_interceptor('.*', dealer=show_view)
        app.add_get_mapping('/', dealer=home, view=homepage)
        with app.test_get('/?who=John', parsejson=False) as ret:
            self.assertEqual(ret, '<John/>')
