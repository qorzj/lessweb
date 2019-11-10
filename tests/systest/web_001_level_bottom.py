import os
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


app = Application()
app.add_get_mapping('/pid', pid)
app.add_get_mapping('.*', f)

if __name__ == '__main__':
    app.run(homepath='/api')
