from unittest import TestCase
from lessweb.application import Application
from lessweb.context import Context
from lessweb.model import request_bridge, fetch_param
from lessweb.storage import Storage


class Test(TestCase):
    def test_request_bridge(self):
        class Person:
            name: str
            age: int
            weight: int

        inputval = {'name': 'Bob', 'age': 33, 'weight': 100, 'x': 1}
        model = request_bridge(inputval, Person)
        self.assertDictEqual(Storage.of(model), {'name': 'Bob', 'age': 33, 'weight': 100})

    def test_fetch_param(self):
        def get_person(ctx: Context, /, name: str, age: int, weight: int, createAt: int = 2):
            pass
        ctx = Context(Application())
        ctx.request.set_alias('weight', 'w')
        ctx.request.param_input.load_query("name=Bob&age=33&w=100&weight=1&createAt=9", encoding='utf8')
        args, param = fetch_param(ctx, get_person)
        self.assertListEqual(args, [ctx])
        self.assertDictEqual(param, {'name': 'Bob', 'age': 33, 'weight': 100, 'createAt': 9})
