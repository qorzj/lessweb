import os
import sys
from lessweb import Application, Context, ResponseStatus


def f(ctx: Context):
    ctx.response.set_status(ResponseStatus(code=201, reason="FOUND"))
    return '\n'.join([
        ctx.request.host,
        ctx.request.protocol,
        ctx.request.homedomain,
        ctx.request.homepath,
        ctx.request.home,
        ctx.request.ip,
        ctx.request.method,
        ctx.request.path,
        ctx.request.query,
        ctx.request.fullpath,
    ])


def pid():
    return f'kill {os.getpid()}'



app = Application(encoding='gb2312')
app.add_patch_mapping('.*', pid)
app.add_get_mapping('.*', f)

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'simple':
        from wsgiref.simple_server import make_server
        make_server('', 8080, app.wsgifunc()).serve_forever()
    else:
        app.run(homepath='/api')
