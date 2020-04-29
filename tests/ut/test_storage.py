from unittest import TestCase
from lessweb.storage import Storage


class Student:
    id: int
    _name: str
    _hide: str = 'yes'
    status: int = 1

    @property
    def name(self) -> str:
        return self._name.upper()

    @name.setter
    def name(self, value) -> None:
        self._name = value


class Test(TestCase):
    def test_success(self):
        self.assertDictEqual({'id': int, 'name': str, 'status': int}, Storage.type_hints(Student))
        student = Storage(id=1, name='John').to(Student)
        self.assertEqual(student.id, 1)
        self.assertEqual(student.name, 'JOHN')
        self.assertEqual(student._hide, 'yes')
        self.assertEqual(student.status, 1)
        self.assertDictEqual({'id': 1, 'name': 'JOHN', 'status': 1}, Storage.of(student))
