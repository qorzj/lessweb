from lessweb.plugin.database import DbServ

import service
from model import Reply, Pager

def list_reply(serv:DbServ, reply:Reply, pager:Pager):
    replys = service.list_reply(serv, reply, pager)
    return {'code': 0, 'list': replys, 'page': pager}