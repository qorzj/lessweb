from unittest import TestCase
from lessweb.context import Context
from lessweb.application import Application, build_controller, interceptor


class Test(TestCase):
    def test_build_controller(self):
        def controller(ctx: Context, id: int, lpn: str):
            return {'ctx': ctx, 'id': id, 'lpn': lpn}
        ctx = Context(Application())
        ctx.request.param_input.load_query("id=5&lpn=HK888", encoding='utf8')
        f = build_controller(controller)
        ret = f(ctx)
        self.assertDictEqual(ret, {'ctx': ctx, 'id': 5, 'lpn': 'HK888'})

    def test_interceptor(self):
        def dealer(ctx: Context, id: int, pageNo: int):
            self.assertEqual((5, 3), (id, pageNo))
            return list(ctx())

        @interceptor(dealer)
        def controller(ctx: Context, id: int, lpn: str):
            return {'ctx': ctx, 'id': id, 'lpn': lpn}
        ctx = Context(Application())
        ctx.request.param_input.load_query("id=5&lpn=HK888&pageNo=3", encoding='utf8')
        ret = build_controller(controller)(ctx)
        self.assertListEqual(ret, ['ctx', 'id', 'lpn'])
