from unittest import TestCase
from enum import Enum
from datetime import datetime

from lessweb.utils import json_dumps
from lessweb.utils import smartenum as se


class Num(Enum):
    one = 1
    two = 2


class TestUtils(TestCase):
    def testJsondumps(self):
        def encode_enum(x:Enum):
            return x.value

        def encode_datetime(x:datetime):
            return x.strftime("%Y-%m-%d %H:%M:%S")



        encoders = [encode_enum, encode_datetime]
        ret = json_dumps([(3, 4), Num.two, datetime(2018,1,31,0,0,0)], encoders=encoders)
        self.assertEquals(ret, '[[3, 4], 2, "2018-01-31 00:00:00"]')

    def testSmartenum(self):
        self.assertTrue(se.one != Num.two)
        self.assertTrue(se.two == Num.two)
        self.assertTrue(se.three != Num.two)
        self.assertTrue(Num.one != se.three)
        self.assertTrue(Num.one != se.two)
        self.assertTrue(Num.one == se.one)
        self.assertTrue(Num.one in [se.three, se.two, se.one])
        self.assertTrue(Num.two not in [se.three, se.one])
