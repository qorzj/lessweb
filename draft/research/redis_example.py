from lessweb import Application
from lessweb.plugin.redisplugin import RedisPlugin, RedisServ


def setter(serv: RedisServ, key:str, value:str):
    serv.redis.set(key, value.encode(), ex=30)
    return 'ok'


def getter(serv: RedisServ, key:str):
    value = serv.redis.get(key)
    if value is None:
        return {}
    return {'key': key, 'value': value.decode()}


app = Application()
app.add_plugin(RedisPlugin('localhost'))
app.add_get_mapping('/set', setter)
app.add_get_mapping('/get', getter)
app.run()


