# lessweb
>「嘞是web」

> "Django lets you write web apps in Django. Flask lets you write web apps in Flask. Lessweb lets you write web apps in Python."

## Get lessweb
```bash
pip3 install lessweb
```

## Hello World!
```python
import lessweb
def hello():
    return 'Hello, world!'

app = lessweb.Application()
app.add_get_mapping('/', hello)
app.run()
```

## 文档：
### http://lessweb.org

## 本地测试步骤：
```bash
virtualenv venv
bash pre_test.sh
. venv/bin/activate
nosetests -s tests/fast_test.py
nosetests -s tests/slow_test.py
nosetests -s tests/final_test.py

```