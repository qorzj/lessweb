from lessweb import Application, Response, Request, HttpStatus

def jump(resp: Response, target):
    resp.set_cookie('token', 'TOKEN_TEXT', expires=10**9, path='/')
    resp.send_redirect(location=target)
    resp.set_status(HttpStatus.SeeOther)
    return ''

def home(req: Request):
    token = req.get_cookie('token')
    return 'hello, %s!' % token

app = Application()
app.add_get_mapping('/jump', jump)
app.add_get_mapping('/', home)

if __name__ == '__main__':
    app.run()