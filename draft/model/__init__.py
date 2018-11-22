from draft.about import *
from enum import Enum

Jsonizable = Union[str, int, bool, Dict, List, None]


class HttpStatus(Enum):
    class Status(NamedTuple):
        code: int
        reason: str

    @staticmethod
    def ofCode(code: int) -> 'HttpStatus':
        for status in HttpStatus:
            if status.value.code == code:
                return status
        raise NotImplementedError(f'HTTP status {code} is not implemented.')

    OK = Status(code=200, reason='OK')
    Created = Status(code=201, reason='Created')
    Accepted = Status(code=202, reason='Accepted')


class Application:
    def set_cast(self, source: Type, target: Type, func: Callable) -> None:
        pass


class UploadedFile:
    filename: str
    value: bytes


class Cookie:
    value: str
    expires: Optional[int] = None
    path: Optional[str] = None
    domain: Optional[str] = None
    secure: bool = False
    httponly: bool = False


class Request:
    def get_cookie(self, name: str) -> Cookie:
        pass

    def get_cookies(self) -> List[Cookie]:
        pass

    def get_header(self, name: str) -> str:
        pass

    def get_headers(self, name: str) -> List[str]:
        pass

    def get_headernames(self) -> List[str]:
        pass


class Response:
    def add_cookie(self, cookie: Cookie) -> None:
        pass

    def contains_header(self, name: str) -> None:
        pass

    def send_redirect(self, location: str) -> None:
        pass

    def set_header(self, name: str, value: Union[str, int]) -> None:
        pass

    def add_header(self, name: str, value: Union[str, int]) -> None:
        pass

    def set_status(self, status: HttpStatus) -> None:
        pass

    def get_status(self) -> HttpStatus:
        pass

    def get_header(self, name: str) -> str:
        pass

    def get_headers(self, name: str) -> List[str]:
        pass

    def get_headernames(self) -> List[str]:
        pass

    def clear_headers(self) -> None:
        pass


class Context:
    request: Request
    response: Response
    application: Application

    def set_param(self, key: Any, realvalue: Any) -> None:
        pass

    def get_param(self, key: Any, default: Any=None) -> Any:
        pass

    def set_alias(self, realname: str, queryname: str) -> None:
        pass

    def get_inputnames(self) -> List[str]:
        pass

    def get_input(self, queryname: str) -> Union[Jsonizable, UploadedFile]:
        pass

    def data(self) -> bytes:
        pass

    def set_cast(self, source: Type, target: Type, func: Callable) -> None:
        pass

    def jsonize(self, value: Any) -> Any:
        pass

    def realname_of(self, queryname: str) -> str:
        pass

    def queryname_of(self, realname: str) -> str:
        pass

    def get_cast(self, source: Type, target: Type) -> Optional[Callable]:
        pass


class NeedParamError(Exception):
    pass


class BadParamError(Exception):
    pass


from abc import ABC


class Model(ABC):
    pass


class Service(ABC):
    pass
