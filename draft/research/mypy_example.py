from lessweb import Application

def f(a: str, b: str):
    return {'c': a + b}

app = Application()
app.add_get_mapping('/', f)

if __name__ == '__main__':
    app.run()
