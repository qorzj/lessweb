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


from .reflect import properties, PropertyType


def parse_timezone(text):
    return Time.fromisoformat(f'00:00:00{text}').tzinfo


def parse_datetime(text, tz) -> Datetime:
    dt = dateutil.parser.isoparse(text)
    return dt.astimezone(tz)


def dump_datetime(data: Datetime, tz) -> str:
    return data.astimezone(tz).isoformat()


def parse_date(text) -> Date:
    return Date.fromisoformat(text)  # can only be isoformat


def dump_date(data: Date):
    return data.isoformat()


def parse_time(text, tz) -> Time:
    return Time.fromisoformat(text).replace(tzinfo=tz)


def dump_time(data: Time, tz) -> str:
    return data.replace(tzinfo=tz).isoformat()


def parse_bool(text) -> bool:
    return {'true': True, 'false': False}[text.lower()]


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


json_basic_types = (bool, int, float, str, list, dict)


class BridgeEncoder(JSONEncoder):
    def default(self, obj):
        if obj is None:
            return obj
        elif isinstance(obj, bytes):
            return base64.b64encode(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, Datetime):
            return dump_datetime(obj, Bridge.tz)
        elif isinstance(obj, Date):
            return dump_date(obj)
        elif isinstance(obj, Time):
            return dump_time(obj, Bridge.tz)
        elif not isinstance(obj, json_basic_types):
            result = {}
            for name in properties(type(obj)).keys():
                value = getattr(obj, name, None)
                if value is not None:
                    result[name] = value
            return result


class Bridge:
    tz = Datetime.now().astimezone().tzinfo

    @classmethod
    def parse(cls, text: str, tp) -> Any:
        if issubclass(tp, bool):
            return parse_bool(text)
        elif issubclass(tp, int):
            return tp(int(text))
        elif issubclass(tp, (str, float, Enum)):
            return tp(text)
        elif tp is Datetime:
            return parse_datetime(text, cls.tz)
        elif tp is Date:
            return parse_date(text)
        elif tp is Time:
            return parse_time(text, cls.tz)
        else:
            raise TypeError(f'unsupported type (got {tp})')

    @classmethod
    def load(cls, json_data, tp: PropertyType) -> Any:
        clfr_type = tp.classifier()
        if isinstance(json_data, list) and issubclass(clfr_type, list):
            tp_args = tp.arguments()
            if not tp_args:
                return json_data
            else:
                return clfr_type(cls.load(item, tp_args[0]) for item in json_data)
        elif isinstance(json_data, clfr_type):
            return clfr_type(json_data)
        elif isinstance(json_data, int) and issubclass(clfr_type, int):
            return clfr_type(json_data)  # e.g. IntEnum
        elif isinstance(json_data, str):
            if clfr_type is bytes:
                return base64.b64decode(json_data)
            elif issubclass(clfr_type, Enum):
                return clfr_type(json_data)
            elif clfr_type is Datetime:
                return parse_datetime(json_data, Bridge.tz)
            elif clfr_type is Date:
                return parse_date(json_data)
            elif clfr_type is Time:
                return parse_time(json_data, Bridge.tz)
            else:
                raise TypeError(f'cannot load str data "{json_data}" to {clfr_type}')
        else:
            result = {}
            for name, member_type in properties(tp.classifier(), tp.arguments()).items():
                value = json_data.get(name)
                if value is None:
                    continue
                result[name] = cls.load(value, member_type)
            return result

    @classmethod
    def dump(cls, type_data) -> Any:  # return: json_data
        return json.loads(json.dumps(type_data, cls=BridgeEncoder))
