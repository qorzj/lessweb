import urllib.parse
from xml.etree.ElementTree import Element, ElementTree


class ParseError(Exception):
    pass


def make_node(key, value):
    node = Element(key)
    if value:
        node.text = value
    return node


def xml_from_params(params: str, root_name='data', encoding='utf-8') -> Element:
    root = Element(root_name)
    param_segs = params.split('&')
    for param_seg in param_segs:
        param_key, param_value = param_seg.split('=', 1) if '=' in param_seg else (param_seg, '')
        param_key = urllib.parse.unquote(param_key, encoding=encoding)
        param_value = urllib.parse.unquote(param_value, encoding=encoding)
        node = make_node(param_key, param_value)
        root.append(node)
    return root


if __name__ == '__main__':
    params = 'title=Everyday%20Italian&author=Giada&price=30.00&title=Harry%20Potter&author=Rowling&price=29.99'
    ret = xml_from_params(params)  # <data><title>Everyday Italian</title><author>Giada</author><price>30.00</price><title>Harry Potter</title><author>Rowling</author><price>29.99</price></data>
