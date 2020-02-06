from lessweb import Application
from lessweb.plugin import redisplugin
from lessweb.plugin.redisplugin import RedisServ


def ping(serv: RedisServ):
  try:
    return serv.redis.ping()
  except:
    return False


redisplugin.init('localhost', port=6379)


def setter(serv: RedisServ, key, value):
    serv.redis.set(key, value.encode(), ex=30)
    return 'ok'

def getter(serv: RedisServ, key):
    value = serv.redis.get(key)
    if value is None:
        return {}
    return {'key': key, 'value': value.decode()}

app = Application()
app.add_interceptor('.*', method='*', dealer=redisplugin.processor)
app.add_get_mapping('/set', setter)
app.add_get_mapping('/get', getter)

app.run()