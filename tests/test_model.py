from unittest import TestCase

from lessweb.utils import _nil
from lessweb.model import RestParam, get_model_parameters, Model


class TestTestModelParameters(TestCase):
    def test_ok(self):
        class _tmp_cls:
            a: int = 1
            b: str
            c = 1
        ret = get_model_parameters(_tmp_cls)
        self.assertEqual(ret, [
            ('a', int, 1), ('b', str, _nil), ('c', _nil, 1)
        ])


class TestModel(TestCase):
    def setUp(self):
        class _tmp_cls(Model):
            a: int = 1
            b: str
            c = 2
            _d: int = 3
        self.model = _tmp_cls()

    def test_items(self):
        self.assertEqual(self.model.storage(), {'a': 1, 'c': 2})

    def test_copy(self):
        model = self.model.copy()
        self.assertEqual(model.storage(), {'a': 1, 'c': 2})
        model2 = self.model.copy(b=3, c=4, _d=5)
        self.assertEqual(model2.storage(), {'a': 1, 'b': 3, 'c': 4})

    def test_setall(self):
        model = self.model.copy()
        self.assertEqual(model.storage(), {'a': 1, 'c': 2})
        model.setall(b=3, c=4, _d=5)
        self.assertEqual(model.storage(), {'a': 1, 'b': 3, 'c': 4})

    def test_eq(self):
        model = self.model.copy()
        self.assertTrue(self.model is not model)
        self.assertEqual(self.model, model)

    def test_repr(self):
        self.assertEqual(repr(self.model), "<Model {'a': 1, 'c': 2}>")
