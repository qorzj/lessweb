from lessweb import Service, Context, HttpStatus, interceptor, Application
from lessweb.plugin import redisplugin
from lessweb.plugin.redisplugin import RedisServ


class LimitServ(Service):
    def __init__(self, redisServ: RedisServ, ctx: Context):
        self.redis = redisServ.redis
        self.ctx = ctx

    @property
    def key(self):
        return f'count/{self.ctx.ip}'

    def touch(self) -> int:
        count = self.redis.get(self.key)
        if count is None:
            count = b'0'
            self.redis.set(self.key, value=count, ex=10)

        self.redis.incr(self.key)
        return int(count.decode())


def limit_checker(ctx: Context, limitServ: LimitServ):
    count = limitServ.touch()
    if count >= 3:
        ctx.response.set_status(HttpStatus.Forbidden)
        return 'Forbidden'
    else:
        return ctx()


@interceptor(redisplugin.processor)
@interceptor(limit_checker)
def hello(serv: LimitServ):
    return 'hello ' + serv.redis.get(serv.key).decode()


redisplugin.init(host='127.0.0.1', port=16379)
app = Application()
app.add_get_mapping('/hello', hello)

if __name__ == '__main__':
    app.run()
