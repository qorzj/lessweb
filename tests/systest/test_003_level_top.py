import os
import requests
import unittest


class TestLevelBottom(unittest.TestCase):
    down_cmd: str

    def setUp(self) -> None:
        os.system("python web_003_level_top.py &")
        os.system("sleep 2")
        self.down_cmd = requests.patch('http://localhost:8080/').text

    def test(self):
        url = 'http://localhost:8080/complex'
        expect_dict = {'result': {'real': 2, 'imag': 4}}
        resp = requests.post(url, {'a': '1,2'})
        self.assertDictEqual(expect_dict, resp.json())

        resp = requests.post(url, json={'a': [1, 2]})
        self.assertDictEqual(expect_dict, resp.json())

        url = 'http://localhost:8080/model'
        expect_dict = {'x': 1, 'y': {'real': 2, 'imag': 3},
                       'z': {'x': 1, 'y': {'real': 2, 'imag': 3}}}
        resp = requests.post(url, {'x': '1', 'y': '2,3'})
        self.assertDictEqual(expect_dict, resp.json())

        resp = requests.post(url, json={'x': 1, 'y': [2, 3]})
        self.assertDictEqual(expect_dict, resp.json())

        url = 'http://localhost:8080/other'
        expect_dict = {'a': False, 'b': 0}
        resp = requests.post(url, {'a': '0', 'b': '0'})
        self.assertDictEqual(expect_dict, resp.json())

        expect_dict = {'a': False, 'b': 0}
        resp = requests.post(url, {'a': '0', 'b': '0'})
        self.assertDictEqual(expect_dict, resp.json())

        expect_dict = {'a': True, 'b': 1}
        resp = requests.post(url, {'a': '✓', 'b': '1'})
        self.assertDictEqual(expect_dict, resp.json())

        expect_dict = {'a': False, 'b': 2}
        resp = requests.post(url, {'a': '✗', 'b': '2'})
        self.assertDictEqual(expect_dict, resp.json())

        resp = requests.post(url, {'a': '✗', 'b': '-1'})
        self.assertEqual(400, resp.status_code)
        self.assertEqual("lessweb.BadParamError query:b error:invalid range for uint(): '-1'", resp.text)

    def tearDown(self) -> None:
        os.system(self.down_cmd)


if __name__ == '__main__':
    unittest.main()
