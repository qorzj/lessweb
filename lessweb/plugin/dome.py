"""
Dom Element
"""
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


def FlexRow(*nodes, id=None):
    return Div(
        *nodes,
        Class='weui-flex', Id=id,
    )


def FlexItem(*nodes, id=None):
    return Div(
        *nodes,
        Class='weui-flex__item', Id=id,
    )


def Button(text, onclick:str, primary=False, warn=False, id=None):
    if primary: btn_class = ' weui-btn_primary'
    elif warn: btn_class = ' weui-btn_warn'
    else: btn_class = ' weui-btn_default'
    return Div(
        text,
        Tag='A', Href=Div.JSVOID, Onclick=onclick, Class='weui-btn weui-btn_mini' + btn_class, Id=id,
    )


def TextInput(title, id):
    return Div(
        Div(
            title,
            Tag='label', Class='weui-cells__title', For=id,
        ), Div(
            Div(
                Div(
                    Div(Tag='input', Id=id, Class='weui-input', Type='text', Placeholder=''),
                    Class='weui-cell__bd'
                ),
                Class='weui-cell',
            ),
            Class='weui-cells',
        )
    )


def TextArea(title, id, rows:int=3):
    return Div(
        Div(
            title,
            Tag='label', Class='weui-cells__title', For=id,
        ), Div(
            Div(
                Div(
                    Div('', Tag='textarea', Id=id, Class='weui-textarea', Placeholder='', Rows=str(rows)),
                    Class='weui-cell__bd',
                ),
                Class='weui-cell',
            ),
            Class='weui-cells weui-cells_form',
        )
    )


def Link(text, url, id=None):
    return Div(text, Tag='a', Href=url, Id=id)


def Module(from_:str, import_:str, as_:str, path='/__target__'):
    """
    example: Module(from_='home', import_='Action()', as_='home_action')
    """
    return Div(
        "import * as "+from_+" from '"+path+"/"+from_+".js'; window."+as_+" = "+from_+"."+import_+";",
        Tag='script', Type='module'
    )


class Kit:
    def ajax(self, method, url, data=None, headers=None, contentType=None, onsuccess=None, onerror=None, **kw):
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

    def get_json(self, url, data, onsuccess):
        """
        :param onsuccess: function(data, status, xhr): when request succeeds
        """
        if not data:
            Zepto.getJSON(url, onsuccess)
        else:
            Zepto.getJSON(url, data, onsuccess)

    def select(self, selector):
        return Zepto(selector)

    def onload(self, handler):
        return Zepto(handler)

    def print(self, obj):
        console.log(obj)

    def alert(self, text, ondone=None):
        if ondone is None:
            weui.alert(text)
        else:
            weui.alert(text, ondone)

    def reload(self, url):
        location.reload(url)

    def goto(self, url):
        location.assign(url)
