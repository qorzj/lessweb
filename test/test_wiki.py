from unittest import TestCase
from lessweb import Application, Response, HttpStatus, UploadedFile, Context


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
