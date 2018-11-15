- Context 上下文对象(含Request和Response)
    - Request
      https://tomcat.apache.org/tomcat-5.5-doc/servletapi/javax/servlet/http/HttpServletRequest.html
    - Response
      https://tomcat.apache.org/tomcat-5.5-doc/servletapi/javax/servlet/http/HttpServletResponse.html
    - setCast(sourceType, targetType, func)  //添加请求级cast
    - jsonize(value)

- Application
    - setCast(sourceType, targetType, func)  //添加全局cast
        - String => Model //解析请求
        - JsonObject => Model //解析json请求
        - Model => JsonObject //返回json对象

- Request
    - getCookie(name: str) -> Cookie
    - getCookies() -> List[Cookie]
    - getHeader(name: str) -> str
    - getHeaders(name: str) -> List[str]
    - getHeaderNames() -> List[str]

- Response
    - addCookie(cookie: Cookie)
    - containsHeader(name: str)
    - sendRedirect(location: str)
    - setHeader(name: str, value: Union[str, int])
    - addHeader(name: str, value: Union[str, int])
    - setStatus(statusCode: int);
    - clearHeaders()
    - getStatus()
    - getHeader(name: str) -> str
    - getHeaders(name: str) -> List[str]
    - getHeaderNames() -> List[str]

- ABC
    - Model
        - 被注入时相当于为成员赋值
        - 有默认的cast函数，相当于java的PO/Map互转
        - 一个非Optional的属性在实例化之后就应该有值
    - Service
        - `__init__`可被注入

- sqlalchemy
    - sqlalchemy.Date.python_type == datetime.date()
    - sqlalchemy.Time.python_type == datetime.time()
    - 重要的文档：
        - https://docs.sqlalchemy.org/en/latest/core/metadata.html (Describing Databases，包括comment)
        - https://docs.sqlalchemy.org/en/latest/core/type_basics.html (Column and Data Types)

- 注入
    - 初始化类型，即是注入一个虚拟的dataclass的`__init__`方法
    - 注入一个函数/方法：
        - Context/Request/Response类: 直接传入上下文对象
        - Model/Service子类: 初始化
        - List/Optional[Model]
        - 其他: 传入cast之后的请求参数
    - optional的Model通过cast获取，非optional的Model通过初始化获取
    - optional的cast可以用非optional的cast
    - 默认级、进程级、请求级的cast要分层
