from lessweb import Application
from http_basic_auth import BaseAuthPlugin


def home():
    return 'Hello, admin!'


app = Application()
app.add_plugin(BaseAuthPlugin(passwords={'admin': '123456'}))
app.add_get_mapping('/', home)
if __name__ == '__main__':
    app.run()