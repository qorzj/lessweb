from lessweb import Application, Context

def admin_hook(ctx: Context):
    ctx.box['me'] = 'admin'
    return ctx()

def home(ctx: Context):
    return 'Hello, %s!' % ctx.box.get('me', 'visitor')


wx_app = Application()
wx_app.add_get_mapping('/hello', home)

admin_app = Application()
admin_app.add_interceptor('.*', '*', admin_hook)
admin_app.add_get_mapping('/hello', home)

if __name__ == '__main__':
    from aiohttp import web
    from aiohttp_wsgi import WSGIHandler

    aioapp = web.Application()
    aioapp.router.add_route("*", "/wx/{path_info:.*}", WSGIHandler(wx_app.wsgifunc()))
    aioapp.router.add_route("*", "/admin/{path_info:.*}", WSGIHandler(admin_app.wsgifunc()))
    web.run_app(aioapp, port=8080)