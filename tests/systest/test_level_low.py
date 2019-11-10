from lessweb import Application, Context


def f(ctx: Context):
    return ctx.request.fullpath


app = Application()
app.add_get_mapping('.*', f)

if __name__ == '__main__':
    app.run()
