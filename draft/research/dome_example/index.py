from lessweb import Application, Response
from lessweb.plugin.dome import HtmlPage
from home import endpoint


app = Application()


def home():
    return HtmlPage(
        *endpoint(),
    ).dumps()


def upper(resp: Response, name: str, intro: str):
    resp.set_header('Content-Type', 'application/json')
    return {'reply': f'{name} {intro}'.upper()}


app.add_get_mapping('/', home)
app.add_post_mapping('/upper', upper)

if __name__ == '__main__':
    from aiohttp import web
    from aiohttp_wsgi import WSGIHandler

    aioapp = web.Application()
    aioapp.router.add_static(prefix='/__target__/', path='__target__')
    aioapp.router.add_route("*", "/{path_info:.*}", WSGIHandler(app.wsgifunc()))
    web.run_app(aioapp, port=8080)
