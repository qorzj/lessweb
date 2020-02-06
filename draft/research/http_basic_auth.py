import base64
import re
from lessweb import Application, Context, HttpStatus

def auth_is_allowed(ctx: Context):
    auth = ctx.env.get('HTTP_AUTHORIZATION')
    if auth is None: return False
    auth = re.sub('^Basic ', '', auth).encode()
    username, password = base64.decodebytes(auth).decode().split(':')
    return username == 'admin' and password == '123456'

def admin_authorise(ctx: Context):
    if not auth_is_allowed(ctx):
        ctx.response.set_header('WWW-Authenticate', 'Basic realm="Auth Example"')
        ctx.response.set_status(HttpStatus.Unauthorized)
    return ctx()

def home():
    return 'Hello, admin!'

app = Application()
app.add_interceptor('.*', '*', admin_authorise)
app.add_get_mapping('/', home)
if __name__ == '__main__':
    app.run()