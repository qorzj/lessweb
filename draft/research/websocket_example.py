import aiohttp.web
from aiohttp_wsgi import WSGIHandler

from lessweb import Application
from lessweb.plugin import redisplugin
from lessweb.plugin.redisplugin import RedisServ

redisplugin.init('localhost', port=6379)

async def websocket_handler(request):
    print('Websocket connection starting')
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    print('Websocket connection ready')

    async for msg in ws:
        print(msg)
        if msg.type == aiohttp.WSMsgType.TEXT:
            print(msg.data)
            if msg.data == 'close':
                await ws.close()
            else:
                who = redisplugin.session().get('who') or b'-'
                await ws.send_str(msg.data + '@' + who.decode())

    print('Websocket connection closed')
    return ws

def setter(serv: RedisServ, who):
    serv.redis.set('who', who.encode(), ex=30)
    return 'ok'

app = Application()
app.add_interceptor('.*', method='*', dealer=redisplugin.processor)
app.add_get_mapping('/set', setter)

if __name__ == '__main__':
    aioapp = aiohttp.web.Application()
    aioapp.router.add_route('GET', '/ws', websocket_handler)
    aioapp.router.add_route("*", "/{path_info:.*}", WSGIHandler(app.wsgifunc()))
    aiohttp.web.run_app(aioapp, port=8080)
