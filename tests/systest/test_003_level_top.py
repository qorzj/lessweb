import os
import requests
import unittest


class TestLevelBottom(unittest.TestCase):
    down_cmd: str

    def setUp(self) -> None:
        os.system("python web_003_level_top.py &")
        os.system("sleep 1")
        self.down_cmd = requests.patch('http://localhost:8080/').text

    def test(self):
        url = 'http://localhost:8080/complex'
        resp = requests.post(url, {'a': '1,2'})
        expect_dict = {'result': {'real': 2, 'imag': 4}}
        self.assertDictEqual(expect_dict, resp.json())

    def tearDown(self) -> None:
        os.system(self.down_cmd)


if __name__ == '__main__':
    unittest.main()
