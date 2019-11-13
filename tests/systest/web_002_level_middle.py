import os
from lessweb import Application, Context, ResponseStatus, ParamStr, MultipartFile


def trans(inputs):
    ret = inputs.copy()
    for key, val in inputs.items():
        for i in range(len(val)):
            ret[key][i] = str(inputs[key][i])
    return str(ret)


def f(ctx: Context):
    return str(ctx.request.param_input.url_input) + '\n' + \
        trans(ctx.request.param_input.query_input) + '\n' + \
        trans(ctx.request.param_input.form_input) + '\n' + \
        str(ctx.request.get_input('m')) + ',' + \
        str(ctx.request.get_input('c')) + ',' + \
        str(ctx.request.get_input('d'))


def g(ctx: Context):
    upload_files = ctx.request.get_multipart_files('a')
    assert isinstance(upload_files, list) and len(upload_files) == 1
    assert upload_files[0].filename == 'a' and upload_files[0].value == b'111'
    return str(ctx.request.param_input.url_input) + '\n' + \
           trans(ctx.request.param_input.query_input) + '\n' + \
           trans(ctx.request.param_input.form_input) + '\n' + \
           str(ctx.request.json_input) + '\n' + \
           trans(ctx.request.file_input) + '\n' + \
           str(ctx.request.is_json()) + '\n' + \
           str(ctx.request.is_form()) + '\n' + \
           str(ctx.request.get_input('a')) + ',' + \
           str(ctx.request.get_input('b'))


def pid():
    return f'kill {os.getpid()}'


app = Application(encoding='gb2312')
app.add_patch_mapping('.*', pid)
app.add_get_mapping('/api/(?P<m>.*)/index.php', f)
app.add_get_mapping('.*', f)
app.add_post_mapping('/(?P<a>.*)/', g)
app.add_post_mapping('/', g)

if __name__ == '__main__':
    app.run()
