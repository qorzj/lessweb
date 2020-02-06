from typing import List, Optional, Union
from unittest import TestCase
from lessweb.typehint import optional_core, generic_core
from lessweb.model import Model


class Test(TestCase):
    def test_optional_core(self):
        type_str = str(optional_core(List[int]))
        self.assertEqual(type_str, "<class 'NoneType'>")
        type_str = str(optional_core(Optional[str]))
        self.assertEqual(type_str, "<class 'str'>")
        type_str = str(optional_core(Union[int, str]))
        self.assertEqual(type_str, "<class 'NoneType'>")

    def test_generic_core(self):
        type_str = str(generic_core(Model[list]))
        self.assertEqual(type_str, "<class 'list'>")
