# 存放与类型转换有关的类型定义，且不依赖同级其他库
from enum import Enum
from datetime import datetime as Datetime, date as Date, time as Time
from json import JSONEncoder
from itertools import chain
from typing import Type, List, Callable, Union, Dict, Any, TypeVar
import base64
import dateutil.parser
import json
from .storage import Storage
from .reflect import PropertyType, properties


__all__ = ["uint", "Jsonizable", "ParamStr", "MultipartFile", "JsonBridgeFunc"]


class uint(int):
    def __init__(self, v):
        super().__init__()
        if self < 0:
            raise ValueError("invalid range for uint(): '%d'" % self)


Jsonizable = Union[str, int, float, Dict, List, None]


class ParamStr(str):
    pass


class MultipartFile:
    filename: str
    value: bytes

    def __init__(self, upfile):
        self.filename = upfile.filename
        self.value = upfile.value

    def __str__(self) -> str:
        return f'<MultipartFile filename={self.filename} value={str(self.value)}>'


JsonBridgeFunc = Callable[[Any], Jsonizable]


def default_response_bridge(obj: Any) -> Jsonizable:
    if isinstance(obj, Datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, bytes):
        return str(obj)
    return None


def make_response_encoder(bridge_funcs: List[JsonBridgeFunc]):
    class ResponseEncoder(JSONEncoder):
        def default(self, obj):
            if obj is None:
                return obj
            for bridge_func in chain(bridge_funcs, [default_response_bridge]):
                dest_val = bridge_func(obj)
                if dest_val is not None:
                    return dest_val
            try:
                if Storage.type_hints(type(obj)):
                    return Storage.of(obj)
            except:
                pass

    return ResponseEncoder


T = TypeVar('T')


def parse_timezone(text):
    return Time.fromisoformat(f'00:00:00{text}').tzinfo


def parse_datetime(text, fmt, tz) -> Datetime:
    if not fmt:
        datetime_val = dateutil.parser.isoparse(text)
    else:
        datetime_val = Datetime.strptime(text, fmt)
    if not datetime_val.tzinfo and tz:
        return datetime_val.replace(tzinfo=parse_timezone(tz))
    else:
        return datetime_val


def dump_datetime(data: Datetime, fmt, tz) -> str:
    if not data.tzinfo and tz:
        data = data.replace(tzinfo=parse_timezone(tz))
    if fmt:
        return data.strftime(fmt)
    else:
        return data.isoformat()


def parse_date(text) -> Date:
    return Date.fromisoformat(text)  # can only be isoformat


def parse_time(text, tz) -> Time:
    if text.endswith('Z'):  # can only be isoformat
        text = text[:-1] + '+00:00'
    time_val = Time.fromisoformat(text)
    if not time_val.tzinfo and tz:
        return time_val.replace(tzinfo=parse_timezone(tz))
    else:
        return time_val


def dump_time(data: Time, tz) -> str:
    if not data.tzinfo and tz:
        data = data.replace(tzinfo=parse_timezone(tz))
    return data.isoformat()


def bridge(data, returntype, *, formatter=None) -> Any:
    """
    :param data: request.headers | request.query | request.match_info | request.json() | request.post()
    :param returntype: Type | PropertyType | Dict[name, Type | PropertyType]
    :param formatter: Dict['date-time' | 'date' | 'time' | 'tz', str | object]
    :param plainmode: plainmode ? from json_str : from json_object
    :return: object or Dict
    """
    if isinstance(returntype, dict):
        if not isinstance(data, dict):
            raise ValueError('data must be dict when returntype is dict')
        ret_dict = {}
        for prop_name, prop_type in returntype.items():
            ret_dict[prop_name] = bridge(data.get(prop_name), prop_type, formatter=formatter)
        return ret_dict
    if not isinstance(returntype, PropertyType):
        returntype = PropertyType(returntype)
    classifier, args_types = returntype.classifier, returntype.arguments
    formatter = formatter or {}
    if data is None and not returntype.nullable:
        raise ValueError('data is None but returntype is not nullable')
    if issubclass(classifier, bool):
        return classifier(data)
    elif issubclass(classifier, int):
        return classifier(int(data))
    elif issubclass(classifier, (str, float, bytes, Datetime, Date, Time)):
        if isinstance(data, classifier):
            return data
        elif issubclass(classifier, (str, float)):
            return classifier(data)
        elif issubclass(classifier, bytes):
            return base64.b64encode(data.encode())  # not support base64
        elif issubclass(classifier, Datetime):
            return parse_datetime(data, formatter.get('date-time'), formatter.get('tz'))
        elif issubclass(classifier, Date):
            return parse_date(data)
        elif issubclass(classifier, Time):
            return parse_time(data, formatter.get('tz'))
        else:  # impossible
            raise NotImplementedError
    elif issubclass(classifier, list):  # json_str or real list ?
        if not data:
            list_data = []
        elif isinstance(data, str):
            list_data = json.loads(data)
        else:
            list_data = list(data)
        if not args_types:
            return list_data
        else:
            return [bridge(item, args_types[0], formatter=formatter) for item in list_data]
    elif issubclass(classifier, dict):  # json_str or real dict ?
        if not data:
            dict_data = {}
        elif isinstance(data, str):
            dict_data = json.loads(data)
        else:
            dict_data = dict(data)
        if not args_types:
            return dict_data
        else:
            return {
                bridge(key, args_types[0], formatter=formatter): bridge(val, args_types[1], formatter=formatter)
                for key, val in dict_data.items()
            }
    elif classifier == Any:
        return data
    else:  # json_str or properties
        if not data:
            dict_data = {}
        elif isinstance(data, str):
            dict_data = json.loads(data)
        else:
            dict_data = dict(data)
        ret_object = classifier()
        ret_dict = bridge(dict_data, properties(classifier), formatter=formatter)
        for key, val in ret_dict.items():
            setattr(ret_object, key, val)
        return ret_object


def dump(data, *, formatter=None, maxdepth=None) -> Any:
    if isinstance(data, (int, str, float)):  # bool is subclass of int
        return data
    elif isinstance(data, bytes):
        return base64.b64decode(data)
    elif isinstance(data, Datetime):
        return dump_datetime(data, formatter.get('date-time'), formatter.get('tz'))
    elif isinstance(data, Date):
        return data.isoformat()
    elif isinstance(data, Time):
        return dump_time(data, formatter.get('tz'))
    elif isinstance(data, dict):
        if maxdepth == 0:
            ...  # TODO
