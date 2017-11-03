# lessweb
>「嘞是web」

> "Django lets you write web apps in Django. Flask lets you write web apps in Flask. Py3web lets you write web apps in Python."

## Hello World!
```python
import lessweb
def hello(ctx):
    return 'Hello, world!'

app = lessweb.Application()
app.add_mapping('/.*', 'GET', hello)
app.run()
```

## 完整示例（简易留言板）：
### https://github.com/qorzj/reply-board

只支持python3.6.0以上版本（目前python3.7有bug）