- Context 上下文对象(含Request和Response)
    - ✓Request
      https://tomcat.apache.org/tomcat-5.5-doc/servletapi/javax/servlet/http/HttpServletRequest.html
    - ✓Response
      https://tomcat.apache.org/tomcat-5.5-doc/servletapi/javax/servlet/http/HttpServletResponse.html
    - ✓set_param/get_param(realname, default=)/get_params()  //保留，但不赋值给dealer
    - ✓input相关：
        - ✓body_data //原来的data
        - ✓get_input(queryname, default=)->Jsonizable
        - ✓get_inputs()->Dict[Jsonizable]

- Application
    - ✓addBridge(...)
        - String => Model //解析请求
        - JsonObject => Model //解析json请求
        - Model => JsonObject //返回json对象
    - ✓encoding要放入header
    - ✓json_encode(Any)->Jsonizable  //暂时没单独做成util的需求

- Request
    - getCookie(name: str) -> Cookie
    - getCookies() -> List[Cookie]
    - containsHeader(name: str)
    - getHeader(name: str) -> str
    - getHeaders(name: str) -> List[str]
    - getHeaderNames() -> List[str]

- Response
    - addCookie(cookie: Cookie)
    - containsHeader(name: str)
    - setHeader(name: str, value: Union[str, int])
    - addHeader(name: str, value: Union[str, int])
    - setStatus(statusCode: int);
    - clearHeaders()
    - getStatus()
    - getHeader(name: str) -> str
    - getHeaders(name: str) -> List[str]
    - getHeaderNames() -> List[str]
    - send*
        - send_access_allow()
        - send_redirect(location: str)

- ABC
    - Model
        - 被注入时相当于为成员赋值
        - 有默认的cast函数，相当于java的PO/Map互转
        - 一个非Optional的属性在实例化之后就应该有值
    - Service
        - `__init__`不变
    - Bridge  # 只负责IO<=>model不负责model<=>dao
        - of(source: Type) -> Bridge
        - to(self: Bridge) -> Type

- sqlalchemy
    - sqlalchemy.Date.python_type == datetime.date()
    - sqlalchemy.Time.python_type == datetime.time()
    - 重要的文档：
        - https://docs.sqlalchemy.org/en/latest/core/metadata.html (Describing Databases，包括comment)
        - https://docs.sqlalchemy.org/en/latest/core/type_basics.html (Column and Data Types)

- 注入
    - 注入一个函数/方法：
        - Context/Request/Response类: 直接传入上下文对象
        - Service子类: 注入`__init__`方法
        - List/Optional[Model]
        - Model子类: 参考spring，不做任何检查(因为技术上无法区分property)，建议只用于post
        - 其他: 传入cast之后的请求参数
    - 删除add_mapping的querynames参数（虽然有些用但不够简洁优雅）
    - addMapping和addBridge的顺序都是找匹配的第一个
    - bridge的of(Union[int, str])支持输入int，to->str支持输出Union[int, str]
