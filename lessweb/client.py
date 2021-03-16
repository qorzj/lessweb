from typing import Any
import math
import json
import requests


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        s = str(obj)
        if len(s) >= 128:
            s = s[:128] + '.' * int(math.log(len(s), 2))
        return s


class Client:
    api_index: dict  # dict[op_id] -> (method, path)
    api_param_indx: dict  # dict[op_id] -> [{name, in}]
    base_url: str
    token: str
    req_data: dict
    resp_data: Any

    def __init__(self, openapi_url, base_url):
        self.api_index = {}
        self.base_url = base_url.rstrip('/')
        self.token = ''
        self.data = None
        openapi_paths = requests.get(openapi_url).json()['paths']
        for path_str, path_value in openapi_paths.items():
            for method, method_value in path_value.items():
                if method not in ['get', 'post', 'put', 'delete']:
                    continue
                op_id = method_value['operationId']
                self.api_index[op_id] = (method, path_str)
                self.api_param_indx[op_id] = path_value.get('parameters', []) + method_value.get('parameters', [])

    def login(self, token: str):
        self.token = token

    def logout(self):
        self.token = ''

    def request(self, op_id, params=None, body=None, expect=200):
        api_method, api_path = self.api_index[op_id]
        path_params = {}
        query_params = {}
        header_params = {}
        is_multipart = False
        if isinstance(params, dict):
            for param_schema in self.api_param_indx[op_id]:
                param_name, param_in = param_schema['name'], param_schema['in']
                if param_name in params:
                    param_value = params.pop(param_name)
                    if param_in == 'path':
                        path_params[param_name] = param_value
                    elif param_in == 'header':
                        header_params[param_name] = str(param_value)
                    elif param_in == 'query':
                        query_params[param_name] = param_value
        if isinstance(body, dict):
            for value in body.values():
                if hasattr(value, 'read') and hasattr(value, 'close'):
                    is_multipart = True
        if path_params:
            url = self.base_url + api_path.format(path_params)
        else:
            url = self.base_url + api_path
        kwargs = {}
        if query_params:
            kwargs['params'] = query_params
        if api_method in ('post', 'put'):
            if is_multipart:
                kwargs['files'] = body  # 例子：{'file': open('/home/data.txt','rb')}
            else:
                kwargs['json'] = body
        if self.token:
            header_params['Authorization'] = f'Bearer {self.token}'
        kwargs['headers'] = header_params
        self.req_data = {**{'method': api_method, 'url': url}, **kwargs}
        resp = requests.request(method=api_method, url=url, **kwargs)
        resp.encoding = 'utf-8'
        assert resp.status_code == expect, f'{op_id}=>[{resp.status_code}] {resp.text}'
        try:
            self.resp_data = resp.json()
        except:
            self.resp_data = resp.text

    def check(self):
        print('>>>> Request')
        print(json.dumps(self.req_data, ensure_ascii=False, indent=2, cls=JsonEncoder))
        print('<<<< Response')
        print(json.dumps(self.resp_data, ensure_ascii=False, indent=2, cls=JsonEncoder))
        try:
            suggest = input('Please input yes/no: ')
            assert suggest.lower() == 'yes'
        except EOFError:
            pass
