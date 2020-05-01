from typing import cast, Dict
from unittest import TestCase
from lessweb.plugin.dbplugin import Mapper
from lessweb.storage import Storage
from sqlalchemy.orm.session import Session


session = Session()


class MockSessionResult:
    def scalar(self) -> int:
        return 1

    def first(self):
        return None

    def __iter__(self):
        return iter([])

    @property
    def lastrowid(self) -> int:
        return 2


class MockSession:
    sql: str
    data: Dict

    def execute(self, sql, data):
        self.sql = sql
        self.data = data
        return MockSessionResult()

    def commit(self):
        pass


class Person:
    id: int
    name: str
    age: int


class Test(TestCase):
    def setUp(self) -> None:
        self.session = MockSession()

    def get_mapper(self):
        return Mapper(cast(Session, self.session), Person)

    def test_bridge(self):
        mapper = self.get_mapper()
        row = {'id': 1, 'name': 'John', 'count': 20}
        student = mapper.bridge(row)
        self.assertDictEqual(Storage.of(student), {'id': 1, 'name': 'John'})

    def test_select_count(self):
        mapper = self.get_mapper()
        n = mapper.select_count()
        self.assertEqual(n, 1)
        self.assertEqual(self.session.sql, 'SELECT COUNT(1) FROM `Person`')
        self.assertDictEqual(self.session.data, {})

        p = Person()
        p.name, p.age = 'Tom', 20
        n = mapper.and_equal(p).select_count()
        self.assertEqual(n, 1)
        self.assertEqual(self.session.sql, 'SELECT COUNT(1) FROM `Person` WHERE (`name`=:name) and (`age`=:age)')
        self.assertDictEqual(self.session.data, {'name': 'Tom', 'age': 20})

        mapper.by_id(42).and_('age=1 or gender=:gender', Storage(gender='M'))
        n = mapper.select_count()
        self.assertEqual(n, 1)
        self.assertEqual(self.session.sql, 'SELECT COUNT(1) FROM `Person` WHERE (`name`=:name) and (`age`=:age) '
                                           'and (`id`=:id) and (age=1 or gender=:gender)')
        self.assertDictEqual(self.session.data, {'name': 'Tom', 'age': 20, 'id': 42, 'gender': 'M'})


    def test_select_first(self):
        obj = self.get_mapper().by_id(42).order_desc().select_first()
        self.assertIsNone(obj)
        self.assertEqual(self.session.sql, 'SELECT `id`,`name`,`age` FROM `Person` WHERE (`id`=:id) '
                                           'ORDER BY `id` desc LIMIT 1')
        self.assertDictEqual(self.session.data, {'id': 42})

    def test_select(self):
        objs = self.get_mapper().by_id(42).order_by('id, name LIMIT 1,2').select()
        self.assertListEqual(objs, [])
        self.assertEqual(self.session.sql, 'SELECT `id`,`name`,`age` FROM `Person` WHERE (`id`=:id) '
                                           'ORDER BY id, name LIMIT 1,2')
        self.assertDictEqual(self.session.data, {'id': 42})

    def test_insert(self):
        p = Person()
        p.name, p.age = 'Tom', 20
        self.get_mapper().insert(p)
        self.assertEqual(self.session.sql, 'INSERT INTO `Person` (`name`,`age`) VALUES (:name,:age)')
        self.assertDictEqual(self.session.data, {'name': 'Tom', 'age': 20})
        self.assertDictEqual(Storage.of(p), {'id': 2, 'name': 'Tom', 'age': 20})

    def test_insert_if_not_exist(self):
        p = Person()
        p.name, p.age = 'Tom', 20
        try:
            self.get_mapper().insert_if_not_exist(p)
        except ValueError as e:
            self.assertEqual(str(e), 'WHERE clause cannot be empty for INSERT_IF_NOT_EXIST!')
        self.get_mapper().and_('name=:name', Storage(name='John')).insert_if_not_exist(p)
        self.assertEqual(self.session.sql, 'INSERT INTO `Person` (`name`,`age`) SELECT :name_1,:age_1 '
                                           'WHERE not exists ( SELECT 1 FROM `Person` WHERE (name=:name))')
        self.assertDictEqual(self.session.data, {'name_1': 'Tom', 'age_1': 20, 'name': 'John'})

    def test_update(self):
        p = Person()
        p.name, p.age = 'Tom', 20
        try:
            self.get_mapper().update(p)
        except ValueError as e:
            self.assertEqual(str(e), 'WHERE clause cannot be empty for UPDATE!')
        self.get_mapper().and_('name=:name', Storage(name='John')).update(p)
        self.assertEqual(self.session.sql, 'UPDATE `Person` SET `name`=:name_1, `age`=:age_1 WHERE (name=:name)')
        self.assertDictEqual(self.session.data, {'name_1': 'Tom', 'age_1': 20, 'name': 'John'})

    def test_increment(self):
        p = Person()
        p.name, p.age = 'Tom', -1
        try:
            self.get_mapper().increment(p)
        except ValueError as e:
            self.assertEqual(str(e), 'WHERE clause cannot be empty for increment UPDATE!')
        self.get_mapper().and_('name=:name', Storage(name='John')).increment(p)
        self.assertEqual(self.session.sql, 'UPDATE `Person` SET `age`=`age`+(:age_1) WHERE (name=:name)')
        self.assertDictEqual(self.session.data, {'age_1': -1, 'name': 'John'})

    def test_delete(self):
        try:
            self.get_mapper().delete()
        except ValueError as e:
            self.assertEqual(str(e), 'WHERE clause cannot be empty for DELETE!')
        p = Person()
        p.name, p.age = 'Tom', 20
        self.get_mapper().and_equal(p).delete()
        self.assertEqual(self.session.sql, 'DELETE FROM `Person` WHERE (`name`=:name) and (`age`=:age)')
        self.assertDictEqual(self.session.data, {'name': 'Tom', 'age': 20})
