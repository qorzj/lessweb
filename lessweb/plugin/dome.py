"""
Dom Element
"""
# __pragma__ ('skip')
import json
# __pragma__ ('noskip')


def uncapitalize_name(name):
    """
        >>> uncapitalize_name("Href")
        'href'
        >>> uncapitalize_name("HttpEquiv")
        'http-equiv'
    """
    buf = []
    for c in name:
        if 'A' <= c <= 'Z' and len(buf):
            buf.append('-')
        buf.append(c)
    return ''.join(buf).lower()


class Div:
    JSVOID = 'javascript:void(0)'

    def __init__(self, *children, **attrs):
        self.children = children
        self.attrs = dict(attrs)
        if 'Tag' in attrs:
            self.tag = uncapitalize_name(attrs['Tag'])
            self.attrs.pop('Tag')
        else:
            self.tag = uncapitalize_name(attrs.get('tag', 'Div'))
            self.attrs.pop('tag', None)

    def _dump_head(self):
        sb = [self.tag]
        for key, value in self.attrs.items():
            if value is not None:
                sb.append(' {}={}'.format(uncapitalize_name(key), repr(value)))
            elif value is True:
                sb.append(' {}'.format(uncapitalize_name(key)))
        return ''.join(sb)

    def dumps(self):
        sb = []
        if self.tag.lower() == 'html':
            sb.append('<!DOCTYPE html>\n')
        if len(self.children):
            sb.append('<{}>'.format(self._dump_head()))
            for child in self.children:
                if isinstance(child, str):
                    sb.append(child)
                elif isinstance(child, Div):
                    sb.append(child.dumps())
                else:
                    sb.append(str(child))
            sb.append('</{}>'.format(self.tag))
            return ''.join(sb)
        else:
            return '<{}/>'.format(self._dump_head())


def HtmlPage(*nodes, title='Welcome', https=False):
    protocol = 'https' if https else 'http'
    return Div(
        Div(
            Div(Tag='meta', Charset='UTF-8'),
            Div(Tag='link', Rel='shortcut icon', Type='image/x-icon', Href='/static/favicon.ico', Media='screen'),
            Div(Tag='meta', HttpEquiv='Cache-Control', Content='no-cache, no-store, must-revalidate'),
            Div(Tag='meta', HttpEquiv='Pragma', Content='no-cache'),
            Div(Tag='meta', HttpEquiv='Expires', Content='0'),
            Div(title, Tag='title'),
            Div(Tag='link', Href=f'{protocol}://res.wx.qq.com/open/libs/weui/1.1.2/weui.min.css', Rel='stylesheet', Type='text/css'),
            Div('', Tag='script', Src=f'{protocol}://cdn.bootcss.com/zepto/1.2.0/zepto.min.js'),
            Div('', Tag='script', Src='https://res.wx.qq.com/open/libs/weuijs/1.1.3/weui.min.js'),
            Div("""
                body {
                    position: relative;
                    width: 100%;
                    height: 100vh;
                    max-width: 640px;
                    margin: 0 auto;
                    margin-bottom: 1.33rem;
                    background-color: #f8f8f8;
                }
                """, Tag='style'
                ),
            Tag='head'
        ),
        Div(
            *nodes,
            Tag='body'
        ),
        Tag='html'
    )


def FlexRow(*nodes, Id=None):
    if len(nodes) == 0:
        nodes = ['']
    return Div(
        *nodes,
        Class='weui-flex', Id=Id,
    )


def FlexItem(*nodes, Id=None):
    if len(nodes) == 0:
        nodes = ['']
    return Div(
        *nodes,
        Class='weui-flex__item', Id=Id,
    )


def Button(text, *, Onclick:str, primary=False, warn=False, Id=None):
    if primary: btn_class = ' weui-btn_primary'
    elif warn: btn_class = ' weui-btn_warn'
    else: btn_class = ' weui-btn_default'
    return Div(
        text,
        Tag='A', Href=Div.JSVOID, Onclick=Onclick, Class='weui-btn weui-btn_mini' + btn_class, Id=Id,
    )


def TextInput(title, *, Id, Name=None, Value=''):
    return Div(
        Div(
            title,
            Tag='label', Class='weui-cells__title', For=Id,
        ), Div(
            Div(
                Div(
                    Div(Tag='input', Id=Id, Class='weui-input', Type='text', Name=Name, Value=Value, Placeholder=''),
                    Class='weui-cell__bd'
                ),
                Class='weui-cell',
            ),
            Class='weui-cells',
        )
    )


def FileInput(title, *, Id, Name=None):
    return Div(
        Div(
            title,
            Tag='label', Class='weui-cells__title',
        ), Div(
            Div(
                Div(
                    Div(Tag='input', Id=Id, Class='weui-input', Type='file', Name=Name),
                    Class='weui-cell__bd'
                ),
                Class='weui-cell',
            ),
            Class='weui-cells',
        )
    )


def TextArea(title, *, Id, Name=None, Rows:int=3):
    return Div(
        Div(
            title,
            Tag='label', Class='weui-cells__title', For=Id,
        ), Div(
            Div(
                Div(
                    Div('', Tag='textarea', Id=Id, Class='weui-textarea', Placeholder='', Name=Name, Rows=str(Rows)),
                    Class='weui-cell__bd',
                ),
                Class='weui-cell',
            ),
            Class='weui-cells weui-cells_form',
        )
    )


def Link(text, *, Url, Id=None):
    return Div(text, Tag='a', Href=Url, Id=Id)


def Module(From:str, Import:str, As:str, Path='/__target__'):
    """
    example: Module(From='home', Import='Action()', AS='home_action')
    """
    return Div(
        "import * as "+From+" from '"+Path+"/"+From+".js'; window."+As+" = "+From+"."+Import+";",
        Tag='script', Type='module'
    )


# Transcrypt only
class Kit:
    @staticmethod
    def ajax(method, url, data=None, headers=None, contentType=None, onsuccess=None, onerror=None, **kw):
        """
        :param onsuccess: function(data, status, xhr): when request succeeds
        :param onerror: function(xhr, errorType, error): timeout, parse error, or status code not in HTTP 2xx
        """
        if method: kw['type'] = method
        if url: kw['url'] = url
        if data is not None: kw['data'] = data
        if headers is not None: kw['headers'] = headers
        if contentType is not None: kw['contentType'] = contentType
        if onsuccess is not None: kw['success'] = onsuccess
        if onerror is not None: kw['error'] = onerror
        Zepto.ajax(kw)

    @staticmethod
    def get_json(url, data, onsuccess):
        """
        :param onsuccess: function(data, status, xhr): when request succeeds
        """
        if not data:
            Zepto.getJSON(url, onsuccess)
        else:
            Zepto.getJSON(url, data, onsuccess)

    @staticmethod
    def select(selector):
        return Zepto(selector)

    @staticmethod
    def onload(handler):
        return Zepto(handler)

    @staticmethod
    def param(data):
        if data is None:
            return None
        tmp = {}
        for k, v in data.items():
            if v is not None:
                tmp[k] = v
        return Zepto.param(tmp)

    @staticmethod
    def parseJSON(text):
        # __pragma__ ('skip')
        if ...: return json.loads(text)
        # __pragma__ ('noskip')
        return Zepto.parseJSON(text)

    @staticmethod
    def stringifyJSON(data):
        # __pragma__ ('skip')
        if...: return json.dumps(data)
        # __pragma__ ('noskip')
        return JSON.stringify(data)

    @staticmethod
    def print(obj):
        console.log(obj)

    @staticmethod
    def alert(text, ondone=None):
        if ondone is None:
            weui.alert(text)
        else:
            weui.alert(text, ondone)

    @staticmethod
    def reload(url):
        location.reload(url)

    @staticmethod
    def goto(url):
        location.assign(url)

    @staticmethod
    def form_data(*selectors):
        formData = eval('new FormData()')
        for selector in selectors:
            div = Kit.select(selector)
            if div.attr('type') == 'file':
                formData.append(div.attr('name'), div[0].files[0])
            else:
                formData.append(div.attr('name'), div.val())
        return formData


# Transcrypt only
class Storage:
    def __init__(self, name, expire=False):
        """
        :param expire: True=sessionStorage, False=localStorage
        """
        self.name = name
        self.expire = expire

    def get(self):
        if self.expire:
            return JSON.parse(sessionStorage.getItem(self.name))
        else:
            return JSON.parse(localStorage.getItem(self.name))

    def set(self, value):
        if self.expire:
            sessionStorage.setItem(self.name, JSON.stringify(value))
        else:
            localStorage.setItem(self.name, JSON.stringify(value))
