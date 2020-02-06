from typing import cast
from unittest import TestCase
from unittest.mock import ANY, DEFAULT, patch
from lessweb import Storage, ChainMock
from lessweb.plugin.database import DbServ

from controller import list_reply
from service import list_reply as service_list_reply
from model import Reply, Pager, TblReply, datetime

class TestListReplyController(TestCase):
    @patch('controller.service.list_reply')
    def test_list_reply(self, list_reply_mock):
        list_reply_mock.side_effect = (
            lambda _, a, b: (
                self.assertEqual((a.nickname, a.age), ('nn', 33)),
                self.assertEqual((b.pageNo, b.pageSize), (3, 4)),
            ) and []
        )
        pager = Pager()
        pager.pageNo = 3; pager.pageSize = 4
        reply = Reply()
        reply.nickname = 'nn'; reply.age = 33
        # CALL controller.list_reply
        serv = cast(DbServ, 'serv')
        ret = list_reply(serv, reply, pager)
        self.assertEqual(ret, {'code': 0, 'list': [], 'page': pager})
        list_reply_mock.assert_any_call(serv, ANY, ANY)

class TestListReplyService(TestCase):
    def setUp(self):
        self.serv = cast(DbServ, Storage())

    def test_list_reply_success(self):
        tbl_reply = TblReply(id=1, nickname='qq', age=25, message='cc', create_at=datetime(2015, 1, 31, 0, 0))

        mock = ChainMock('query.filter.order_by.offset.limit.all', [tbl_reply]).join('query.filter.order_by.count', 3)
        mock('query.filter.order_by').side_effect = lambda a: self.assertEqual(str(a), 'reply.id DESC') or DEFAULT
        mock('query.filter').side_effect = (
            lambda a, b: (
                self.assertEqual(str(a), 'reply.nickname = :nickname_1'),
                self.assertEqual(a.compile().params, {'nickname_1': 'aa'}),
                self.assertEqual(str(b), 'reply.age = :age_1'),
                self.assertEqual(b.compile().params, {'age_1': 25}),
            ) and DEFAULT
        )

        self.serv.db = Storage(query=mock('query'))
        reply = Reply()
        reply.nickname = 'aa'; reply.age = 25
        reply_expect = Reply()
        reply_expect.id = 1; reply_expect.nickname = 'qq'; reply_expect.age = 25; reply_expect.message = 'cc'
        reply_expect.create_at = datetime(2015, 1, 31, 0, 0)
        pager = Pager()
        pager.pageNo = 2; pager.pageSize = 10
        # CALL service.list_reply
        replys = service_list_reply(self.serv, reply, pager)
        self.assertEqual(replys, [reply_expect])
        self.assertEqual(pager.total, 3)
        mock('query.filter.order_by.count').assert_called_once_with()
        mock('query.filter.order_by.offset').assert_called_once_with(10)
        mock('query.filter.order_by.offset.limit').assert_called_once_with(10)
        mock('query.filter.order_by.offset.limit.all').assert_called_once_with()
