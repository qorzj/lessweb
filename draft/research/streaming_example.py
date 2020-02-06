import time
from lessweb import Application, Context, interceptor
from wsgiref.simple_server import make_server

def wrap_map(ctx:Context):
    def mapper(x):
        yield '['
        yield from x
        yield ']'
    return mapper(ctx())

def upper_map(ctx:Context):
    return (c.upper() for c in ctx())

@interceptor(wrap_map)
@interceptor(upper_map)
def stream(n:int):
    for i in range(n):
        yield chr(ord('a') + i)
        time.sleep(1)

app = Application()
app.add_get_mapping('/stream/{n}', stream)
if __name__ == '__main__':
    make_server('', 8080, app.wsgifunc()).serve_forever()
