from lessweb.application import Application


def f(x: int = 1):
    return {'x': x}


app = Application()
app.add_get_mapping('/', dealer=f)
app.run()
