import urllib.parse
from xml.etree.ElementTree import Element, ElementTree


class ParseError(Exception):
    pass


def make_node(key, value):
    node = Element(key)
    if value:
        node.text = value
    return node


def array_startswith(arr, prefix_arr):
    prefix_len = len(prefix_arr)
    return len(arr) >= prefix_len and arr[:prefix_len] == prefix_arr


def xml_from_params(params: str, root_name='data', encoding='utf-8') -> Element:
    root = Element(root_name)
    param_segs = params.split('&')
    stack = []  # (key, node)
    for param_seg in param_segs:
        param_key, param_value = param_seg.split('=', 1) if '=' in param_seg else (param_seg, '')
        param_key = urllib.parse.unquote(param_key)
        param_value = urllib.parse.unquote(param_value)
        param_key_segs = param_key.split('.')
        if not param_key_segs or any(not(seg) for seg in param_key_segs):
            raise ParseError('empty param key')
        node = make_node(param_key, param_value)
        print(stack, param_key, param_value)
        if stack and array_startswith(param_key_segs, stack):
            stack[-1][1].append(node)
        elif len(param_key_segs) == len(stack) + 1:
            stack.append((param_key_segs[-1], node))
        elif len(param_key_segs) == len(stack):
            stack[-1] = (param_key_segs[-1], node)
        else:
            raise ParseError('parse failed')
    return root


if __name__ == '__main__':
    params = 'book&book.title=Everyday%20Italian&book.author=Giada&book.price=30.00&book&book.title=Harry%20Potter&book.author=Rowling&book.price=29.99'
    xml_from_params(params)
