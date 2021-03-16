import aiohttp.web
import requests

from lessweb.schemavalid import make_resolver, validate, check_param_str
from lessweb.utils import func_arg_spec


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
        result = await callback_func(*poargs, **kwargs)
        return aiohttp.web.json_response(result)
