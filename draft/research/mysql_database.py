import sys
sys.path.append('.')
from lessweb import Application
from lessweb.plugin import database
from lessweb.plugin.database import DbServ

from sqlalchemy import Column, Integer, Text, String, Enum as ENUM, func, UniqueConstraint
from lessweb.plugin.database import DbModel, cast_model
from lessweb import Model
from enum import Enum


class Gender(Enum):
    MALE = 1
    FEMALE = 2


class TblBook(DbModel):  # 表名默认为'TblBook'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    author = Column(String(64))
    __table_args__ = (UniqueConstraint('id', 'author', name='_uniq_id_author'),)


class TblUser(DbModel):
    __tablename__ = 'tbl_user'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), comment='姓名')
    gender = Column(ENUM(Gender))


class Book(Model):  # 用途：与前端交互
    id: int
    name: str
    author: str


def book_detail_a(serv:DbServ, id:int):
    ret = serv.db.execute('SELECT * FROM TblBook WHERE id=:id', {'id': id}).first()
    return str(ret)


def book_detail_b(serv:DbServ, id:int):
    tblBook = serv.db.query(TblBook, func.concat(TblBook.author, '!').label('author')).filter(TblBook.id == id).first()
    print(type(tblBook))
    book = cast_model(Book, tblBook)
    return {'code': 200, 'result': book}

database.init(
  protocol='mysql+mysqlconnector',
  username='root', password='pwd',
  host='localhost', port=3306, database='proj', echo=True,
  autoflush=True, autocommit=False
)

app = Application()
app.add_interceptor('.*', method='*', dealer=database.processor)
app.add_get_mapping('/book/{id}', book_detail_b)
database.create_all(TblBook, TblUser)
app.run()
