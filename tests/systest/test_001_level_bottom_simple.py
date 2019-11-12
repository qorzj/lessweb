import os
import requests
import unittest


# 测试用wsgiref.simple_server代替aiohttp的情况
# 默认path编码为ISO-8859-1，且无REQUEST_URI，因此path上不支持非ASCII文本
class TestLevelBottomSimple(unittest.TestCase):
    down_cmd: str

    def setUp(self) -> None:
        os.system("python web_001_level_bottom.py simple &")
        os.system("sleep 1")
        self.down_cmd = requests.patch('http://localhost:8080/').text

    def test(self):
        url = 'http://localhost:8080/api/hello/index.php?m=admin&c=index&a=%C4%E3%BA%C3'
        resp = requests.get(url)
        self.assertEqual(201, resp.status_code)
        self.assertEqual('FOUND', resp.reason)
        expect_text = """localhost:8080
http
http://localhost:8080

http://localhost:8080
127.0.0.1
GET
/api/hello/index.php
m=admin&c=index&a=%C4%E3%BA%C3
http://localhost:8080"""
        self.assertEqual(expect_text, resp.text)

    def tearDown(self) -> None:
        os.system(self.down_cmd)

if __name__ == '__main__':
    unittest.main()
