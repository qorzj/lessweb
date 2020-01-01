from os import system, listdir
from unittest import TestCase


class SlowTest(TestCase):
    """
    各种使用情景的mypy测试和接口测试
    """
    def setUp(self):
        system("pip install -q -e .")

    def testTypeSafe(self):
        self.assertEqual(0, system("cd tests/typesafe && mypy *"))

        for filename in listdir("tests/typeunsafe"):
            if filename.startswith('test_'):
                self.assertNotEqual(0, system(f"cd tests/typeunsafe && mypy {filename}"))

        self.assertEqual(0, system("cd tests/systest && nosetests -s *"))

    def tearDown(self):
        system("pip uninstall -y -q lessweb")
