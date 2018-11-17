"""
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base, as_declarative, declared_attr

dburi = 'mysql+mysqlconnector://root:ParSEC%4020%2317@rm-bp1wyk9zedimcu84fo.mysql.rds.aliyuncs.com:3306/smscaptcha'
engine = create_engine(dburi, pool_recycle=3600)
engine.echo = True
db_session_maker = scoped_session(sessionmaker(autoflush=True, autocommit=True, bind=engine))


@as_declarative()
class DbBase(object):
    @declared_attr
    def __tablename__(cls):
        return 'tbl_' + cls.__name__.lower()

    def __repr__(self):
        return '<DbModel ' + repr(list(self.__dict__.items())) + '>'


class Dburi(DbBase):
    id = Column(Integer, primary_key=True)
    name = Column(String(200))


if __name__ == 'zz__main__':
    db: Session = db_session_maker()
    with db.begin():
        ret = db.execute("insert into tbl_dburi values()")
        row = db.query(Dburi).filter_by(id=ret.lastrowid).first()
        row.name = 'parsec.com.cn'

    print('DONE.')
"""

if __name__ == '__main__':
    from sqlalchemy import create_engine, Column, Integer, String
    from dataclasses import dataclass, asdict

    def At(x): return x

    @dataclass
    class StructOfPriceName:
        At(Column(Integer))
        price: int

        name: str

    def foo(**a):
        print(a)

    if...: # test
        # /*价格*/ price /*名称*/ name #
        foo(**asdict(StructOfPriceName(price=15, name="abc")))

        print(1, 2, 3)

