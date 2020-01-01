from unittest import TestCase
from lessweb.application import Application
from lessweb.context import Context
from lessweb.bridge import RequestBridge
from lessweb.model import fetch_model, fetch_param, Model
from lessweb.storage import Storage


class Test(TestCase):
    def test_fetch_model(self):
        class Person:
            name: str
            age: int
            weight: int

        ctx = Context(Application())
        ctx.request.set_alias('weight', 'w')
        ctx.request.param_input.load_query("name=Bob&age=33&w=100&x=1", encoding='utf8')
        model = fetch_model(ctx, RequestBridge([]), Person, Model)
        self.assertDictEqual(Storage.of(model.get()), {'name': 'Bob', 'age': 33, 'weight': 100})

    def test_fetch_param(self):
        def get_person(ctx: Context, name: str, age: int, weight: int, createAt: int = 2):
            pass
        ctx = Context(Application())
        ctx.request.set_alias('weight', 'w')
        ctx.request.param_input.load_query("name=Bob&age=33&w=100&weight=1&createAt=9", encoding='utf8')
        param = fetch_param(ctx, get_person)
        self.assertDictEqual(param, {'ctx': ctx, 'name': 'Bob', 'age': 33, 'weight': 100, 'createAt': 9})