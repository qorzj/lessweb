import os
import requests
import unittest


class TestLevelBottom(unittest.TestCase):
    down_cmd: str

    def setUp(self) -> None:
        os.system("python web_001_level_bottom.py &")
        os.system("sleep 2")
        self.down_cmd = requests.patch('http://localhost:8080/api/').text

    def test(self):
        url = 'http://localhost:8080/api/%C4%E3%BA%C3/index.php?m=admin&c=index&a=%C4%E3%BA%C3'
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
m=admin&c=index&a=%C4%E3%BA%C3
http://localhost:8080/api/%C4%E3%BA%C3/index.php?m=admin&c=index&a=%C4%E3%BA%C3"""
        self.assertEqual(expect_text, resp.text)

    def tearDown(self) -> None:
        os.system(self.down_cmd)

if __name__ == '__main__':
    unittest.main()
