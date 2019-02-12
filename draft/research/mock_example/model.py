from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from lessweb import Model
from lessweb.plugin.database import DbModel

class Pager(Model):
    pageNo: int = 1
    pageSize: int = 10
    total: int = 0
    totalPage: int = 1

    def slice(self, ordered_query):
        self.total = ordered_query.count()
        self.pageNo = max(self.pageNo, 1)
        self.pageSize = min(max(self.pageSize, 1), 200)
        self.totalPage = (self.total + self.pageSize - 1) // self.pageSize
        return ordered_query.offset((self.pageNo - 1) * self.pageSize).limit(self.pageSize).all()

class Reply(Model):
    id: int
    nickname: str
    age: int
    message: str
    create_at: datetime


class TblReply(DbModel):
    __tablename__ = 'reply'
    id = Column(Integer, primary_key=True)
    nickname = Column(String(200))
    age = Column(Integer)
    gender = Column(Integer)
    message = Column(Text)
    create_at = Column(DateTime)
