#!/usr/bin/env bash
. venv/bin/activate
pip install nose
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mypy
pip install aiohttp
pip install aiohttp_wsgi
pip install requests
pip install typing_inspect
pip install redis
pip install sqlalchemy-stubs