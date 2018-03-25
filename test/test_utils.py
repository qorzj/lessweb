from unittest import TestCase
from enum import Enum
from datetime import datetime

from lessweb.utils import json_dumps
from lessweb.utils import anyenum as ae


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
        self.assertTrue(ae.one != Num.two)
        self.assertTrue(ae.two == Num.two)
        self.assertTrue(ae.three != Num.two)
        self.assertTrue(Num.one != ae.three)
        self.assertTrue(Num.one != ae.two)
        self.assertTrue(Num.one == ae.one)
        self.assertTrue(Num.one in [ae.three, ae.two, ae.one])
        self.assertTrue(Num.two not in [ae.three, ae.one])
