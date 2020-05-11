# lessweb
>「嘞是web」

> A pythonic web framework

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
### http://www.lessweb.cn

## 本地测试步骤：
```bash
virtualenv venv
. venv/bin/activate
bash pre_test.sh
nosetests -s tests/fast_test.py
nosetests -s tests/slow_test.py
nosetests -s tests/final_test.py

```