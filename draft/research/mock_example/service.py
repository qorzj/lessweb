from sqlalchemy import desc
from lessweb.plugin.database import DbServ, cast_models
from model import Reply, TblReply, Pager

def list_reply(serv:DbServ, reply:Reply, pager: Pager):
    def get_filters():
        if reply.nickname: yield TblReply.nickname == reply.nickname
        if reply.age: yield TblReply.age == reply.age

    query = serv.db.query(TblReply).filter(*get_filters()).order_by(desc(TblReply.id))
    rows = pager.slice(ordered_query=query)
    replys = cast_models(Reply, rows)
    return replys
