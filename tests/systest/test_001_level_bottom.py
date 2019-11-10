import os
import requests
import unittest


class TestLevelBottom(unittest.TestCase):
    down_cmd: str

    def setUp(self) -> None:
        os.system("python web_001_level_bottom.py &")
        os.system("sleep 1")
        self.down_cmd = requests.get('http://localhost:8080/api/pid').text

    def test(self):
        url = 'http://localhost:8080/api/%E4%BD%A0%E5%A5%BD/index.php?m=admin&c=index&a=%E7%A7%92%E5%B7%AE%E8%B7%9D'
        resp = requests.get(url)
        self.assertEqual(201, resp.status_code)
        self.assertEqual('FOUND', resp.reason)
        expect_text = """localhost:8080
http
http://localhost:8080
/api
http://localhost:8080/api
127.0.0.1
GET
/你好/index.php
m=admin&c=index&a=%E7%A7%92%E5%B7%AE%E8%B7%9D
http://localhost:8080/api/%E4%BD%A0%E5%A5%BD/index.php?m=admin&c=index&a=%E7%A7%92%E5%B7%AE%E8%B7%9D"""
        self.assertEqual(expect_text, resp.text)

    def tearDown(self) -> None:
        os.system(self.down_cmd)

if __name__ == '__main__':
    unittest.main()
