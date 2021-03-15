from typing import Any
import math
import json
import requests
import aiohttp.web
from .utils import func_arg_spec
from .schemavalid import make_resolver, check_param_str, validate


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


class Service:
    openapi_data: dict
    api_index: dict  # dict[op_id] -> [callback}]
    api_param_indx: dict  # dict[op_id] -> [{name, in, schema}]
    api_rev_index: dict  # dict[method, path] -> op_id

    def __init__(self, openapi_url):
        self.api_index = {}
        self.api_rev_index = {}
        self.api_param_indx = {}
        self.api_schema_index = {}

        self.openapi_data = requests.get(openapi_url).json()
        self.resolver = make_resolver(self.openapi_data)
        openapi_paths = self.openapi_data['paths']
        for path_str, path_value in openapi_paths.items():
            for method, method_value in path_value.items():
                if method not in ['get', 'post', 'put', 'delete']:
                    continue
                op_id = method_value['operationId']
                self.api_param_indx[method, path_str] = op_id
                self.api_index[op_id] = (method, path_str)
                self.api_param_indx[op_id] = path_value.get('parameters', []) + method_value.get('parameters', [])
                try:
                    req_content_dict = method_value['requestBody']['content']
                    for content_key, content_val in req_content_dict.items():
                        if content_key.lower() in ('application/json', '*/*'):
                            self.api_schema_index[op_id] = content_val['schema']
                            break
                except:
                    pass

    def endpoint(self, op_id):
        def g(f):
            self.api_index[op_id] = f
            return f
        return g

    def response(self, request: aiohttp.web.Request, context=None):
        method = request.method
        path_pattern = request.match_info.get_info()['formatter']
        op_id = self.api_rev_index.get((method, path_pattern))
        if op_id is None:
            raise aiohttp.web.HTTPBadRequest(text=f'operation {method} {path_pattern} is undefined')
        params = self.api_param_indx[method, path_pattern]
        callback_func = self.api_index[op_id]
        poargs = []
        kwargs = {}
        using_names = set()
        for realname, (_, _, positional_only) in func_arg_spec(callback_func).items():
            if positional_only and op_id in self.api_schema_index:
                req_json = await request.json()
                validate(req_json, schema=self.api_schema_index[op_id], resolver=self.resolver)
                poargs.append(req_json)
            else:
                using_names.add(realname)
        if context and isinstance(context, dict):
            kwargs.update(context)
        for param_dict in params:
            param_name = param_dict['name']
            if param_name in kwargs or param_name not in using_names:
                continue
            param_in = param_dict.get('in', 'query')
            param_required = param_dict.get('required', False)
            if param_in == 'header':
                param_value = request.headers.get(param_name)
            elif param_in == 'cookie':
                param_value = request.cookies.get(param_name)
            elif param_in == 'path':
                param_value = request.match_info.get(param_name)
            else:
                param_value = request.query.get(param_name)
            if param_required and param_value is None:
                raise aiohttp.web.HTTPBadRequest(text=f'{param_in} param [{param_name}] is required')
            if not param_dict.get('allowEmptyValue', True) and not param_value:
                raise aiohttp.web.HTTPBadRequest(text='allowEmptyValue is true but param is empty')
            real_value = check_param_str(param_name, param_value=param_value, schema=param_dict['schema'], resolver=self.resolver)
            kwargs[param_name] = real_value
        result = callback_func(*poargs, **kwargs)
        return aiohttp.web.json_response(result)
