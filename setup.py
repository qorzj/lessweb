from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
import os
from os import path
from setuptools.command.install import install
import re
import ast

_version_re = re.compile(r'__version__\s+=\s+(.*)')
version = str(ast.literal_eval(
    _version_re.search(
        open('lessweb/__init__.py').read()
    ).group(1)
))
here = path.abspath(path.dirname(__file__))


def find_stub_files():
    result = []
    for root, dirs, files in os.walk('lessweb-stubs'):
        for file in files:
            if file.endswith('.pyi'):
                if os.path.sep in root:
                    sub_root = root.split(os.path.sep, 1)[-1]
                    file = os.path.join(sub_root, file)
                result.append(file)
    return result


class MyInstall(install):
    def run(self):
        print("-- installing... --")
        install.run(self)

setup(
        name = 'lessweb',
        version=version,
        description='A pythonic web framework 「嘞是web」',
        long_description='\nREADME: https://github.com/qorzj/lessweb\n\n'
                         'Cookbook: http://www.lessweb.cn',
        url='https://github.com/qorzj/lessweb',
        author='qorzj',
        author_email='inull@qq.com',
        license='MIT',
        platforms=['any'],

        classifiers=[
            ],
        keywords='lessweb web web.py',
        packages = ['lessweb', 'lessweb.plugin', 'lessweb-stubs'],
        package_data={'lessweb-stubs': find_stub_files()},
        install_requires=['aiohttp', 'aiohttp_wsgi', 'requests', 'typing_inspect', 'typing_extensions'],

        cmdclass={'install': MyInstall},
        entry_points={
            'console_scripts': [
                ],
            },
    )
