from typing import List, Optional, Union, ClassVar, Callable, TypeVar
from unittest import TestCase
from lessweb.typehint import optional_core, generic_core, is_generic_type, get_origin


T = TypeVar('T')


class Test(TestCase):
    def test_optional_core(self):
        is_optional, core_type = optional_core(List[int])
        self.assertFalse(is_optional)
        self.assertEqual(str(core_type), "typing.List[int]")
        is_optional, core_type = optional_core(Optional[str])
        self.assertTrue(is_optional)
        self.assertEqual(str(core_type), "<class 'str'>")
        is_optional, core_type = optional_core(Union[int, str])
        self.assertFalse(is_optional)
        self.assertEqual(str(core_type), "typing.Union[int, str]")

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
        core_type = generic_core(List[bool])
        self.assertEqual(str(core_type), "<class 'bool'>")
