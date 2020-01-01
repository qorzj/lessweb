from os import system
from unittest import TestCase


class FastTest(TestCase):
    """
    lessweb本身的mypy检查和单测
    """
    def setUp(self):
        print("setup")

    def testMypy(self):
        self.assertEqual(0, system("mypy lessweb"))

    def testUT(self):
        self.assertEqual(0, system("nosetests -s tests/ut"))

    def tearDown(self):
        print("tear down")
