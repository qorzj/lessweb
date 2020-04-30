from typing import List, Optional, Union, ClassVar, Callable, TypeVar
from unittest import TestCase
from lessweb.typehint import optional_core, generic_core, is_generic_type, get_origin


T = TypeVar('T')


class Test(TestCase):
    def test_optional_core(self):
        type_str = str(optional_core(List[int]))
        self.assertEqual(type_str, "<class 'NoneType'>")
        type_str = str(optional_core(Optional[str]))
        self.assertEqual(type_str, "<class 'str'>")
        type_str = str(optional_core(Union[int, str]))
        self.assertEqual(type_str, "<class 'NoneType'>")

    def test_generic_core(self):
        self.assertFalse(is_generic_type(int))
        self.assertFalse(is_generic_type(Union[int, str]))
        self.assertFalse(is_generic_type(Union[int, T]))
        self.assertFalse(is_generic_type(ClassVar[List[int]]))
        self.assertFalse(is_generic_type(Callable[..., T]))
        self.assertFalse(is_generic_type(bool))
        self.assertFalse(is_generic_type(list))
        self.assertTrue(is_generic_type, List[bool])
        self.assertEqual(get_origin(list), None)
        self.assertEqual(get_origin(bool), None)
        self.assertEqual(get_origin(List[bool]), list)
        type_str = str(generic_core(List[bool]))
        self.assertEqual(type_str, "<class 'bool'>")
