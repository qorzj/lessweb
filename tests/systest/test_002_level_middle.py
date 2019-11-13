import os
import requests
import unittest


class TestLevelBottom(unittest.TestCase):
    down_cmd: str

    def setUp(self) -> None:
        os.system("python web_002_level_middle.py &")
        os.system("sleep 1")
        self.down_cmd = requests.patch('http://localhost:8080/api/').text

    def test(self):
        url = 'http://localhost:8080/api/%C4%E3%BA%C3/index.php?m=admin&c=index&a=%C4%E3%BA%C3&m=add'
        resp = requests.get(url)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('OK', resp.reason)
        expect_text = """{'m': '你好'}
{'m': ['admin', 'add'], 'c': ['index'], 'a': ['你好']}
{}
你好,index,None"""
        self.assertEqual(expect_text, resp.text)

        url = 'http://localhost:8080/yz/?a=xy&a=wx'
        resp = requests.post(url, {'a': 'vw'}, files={'a': b'111'})
        expect_text = """{'a': 'yz'}
{'a': ['xy', 'wx']}
{'a': ['xy', 'wx', 'vw']}
None
{'a': ["<MultipartFile filename=a value=b'111'>"]}
False
True
yz,None"""
        self.assertEqual(expect_text, resp.text)

        url = 'http://localhost:8080?a=xy&a=wx'
        resp = requests.post(url, {'a': 'vw'}, files={'a': b'111'})
        expect_text = """{}
{'a': ['xy', 'wx']}
{'a': ['xy', 'wx', 'vw']}
None
{'a': ["<MultipartFile filename=a value=b'111'>"]}
False
True
xy,None"""
        self.assertEqual(expect_text, resp.text)

        url = 'http://localhost:8080?b=xy&b=wx'
        resp = requests.post(url, {'a': 'vw'}, files={'a': b'111'})
        expect_text = """{}
{'b': ['xy', 'wx']}
{'a': ['vw'], 'b': ['xy', 'wx']}
None
{'a': ["<MultipartFile filename=a value=b'111'>"]}
False
True
vw,xy"""
        self.assertEqual(expect_text, resp.text)

        url = 'http://localhost:8080?b=xy&b=wx'
        resp = requests.post(url, {'b': 'vw'}, files={'a': b'111'})
        expect_text = """{}
{'b': ['xy', 'wx']}
{'b': ['xy', 'wx', 'vw']}
None
{'a': ["<MultipartFile filename=a value=b'111'>"]}
False
True
None,xy"""
        self.assertEqual(expect_text, resp.text)

    def tearDown(self) -> None:
        os.system(self.down_cmd)


if __name__ == '__main__':
    unittest.main()
