from unittest import TestCase
from lessweb.sugar import _ext


class TestExt(TestCase):
    def testOK(self):
        self.assertEqual('abc' @ _ext(len), 3)
        self.assertListEqual([3,1,2] @ _ext(sorted, key=lambda x: -x), [3, 2, 1])
