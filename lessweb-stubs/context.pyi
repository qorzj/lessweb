from typing import Any, Optional, Dict, List, Union, TYPE_CHECKING
from requests.structures import CaseInsensitiveDict

from lessweb.webapi import Cookie, HttpStatus, ResponseStatus, ParamInput
from lessweb.bridge import Jsonizable, ParamStr, MultipartFile


__all__ = ["Request", "Response", "Context"]


if TYPE_CHECKING:
    from lessweb.application import Application


class Request:
    _cookies: Dict[str, str]
    _aliases: Dict[str, str]
    _params: Dict[str, Union[ParamStr, Jsonizable, None]]
    encoding: str
    environ: Dict
    env: Dict
    host: str
    protocol: str
    homedomain: str
    homepath: str
    home: str
    ip: str
    method: str
    path: str
    query: str
    fullpath: str
    body_data: Optional[bytes]
    json_input: Optional[Dict]
    param_input: ParamInput
    file_input: Dict[str, List[MultipartFile]]
    def __init__(self, encoding: str) -> None: ...
    def load(self, env) -> None: ...
    def set_alias(self, realname, queryname) -> None: ...
    def is_json(self) -> bool: ...
    def is_form(self) -> bool: ...
    def contains_cookie(self, name: str) -> bool: ...
    def get_cookie(self, name: str) -> Optional[str]: ...
    def get_cookienames(self) -> List[str]: ...
    def contains_header(self, name: str) -> bool: ...
    def get_header(self, name: str) -> Optional[str]: ...
    def get_headernames(self) -> List[str]: ...
    def get_input(self, key: str) -> Optional[Union[ParamStr, Jsonizable]]: ...
    def get_uploaded_files(self, key: str) -> List[MultipartFile]: ...


class Response:
    _cookies: Dict[str, Cookie]
    _status: Union[HttpStatus, ResponseStatus]
    _headers: CaseInsensitiveDict
    encoding: str
    def __init__(self, encoding: str) -> None: ...
    def set_cookie(self, name:str, value:str, expires:int=None, path:str='/',
                   domain:str=None, secure:bool=False, httponly:bool=False) -> None: ...
    def get_cookie(self, name:str) -> Optional[Cookie]: ...
    def del_cookie(self, name:str) -> None: ...
    def set_status(self, status: Union[HttpStatus, ResponseStatus]) -> None: ...
    def get_status(self) -> Union[HttpStatus, ResponseStatus]: ...
    def set_header(self, name: str, value: Union[str, int]) -> None: ...
    def get_header(self, name: str) -> Optional[str]: ...
    def del_header(self, name: str) -> str: ...
    def get_headernames(self) -> List[str]: ...
    def clear(self) -> None: ...
    def send_access_allow(self, allow_headers: List[str]=None) -> None: ...
    def send_allow_methods(self, methods: List[str]) -> None: ...
    def send_redirect(self, location: str) -> None: ...
    def send_content_type(self, mimekey='html', encoding: str='') -> None: ...


class Context(object):
    app_stack: List
    app: Application
    request: Request
    response: Response
    box: Dict
    def __init__(self, app: 'Application') -> None: ...
    def __call__(self) -> Any: ...

