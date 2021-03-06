import os
from lessweb import Application, Context, Request, ResponseStatus, ParamStr, MultipartFile, uint


def load_complex(n, real_type):
    if real_type == complex:
        if isinstance(n, ParamStr):
            real, imag = n.split(',', 1)
            return complex(int(real), int(imag))
        else:
            return complex(n[0], n[1])


def dump_complex(n):
    if isinstance(n, complex):
        return {'real': n.real, 'imag': n.imag}


class A:
    x: int
    y: complex

    def __str__(self):
        return str(self.x * self.y)


def f(a: complex = None):
    if a is None:
        return {'result': None}
    else:
        return {'result': a * 2}


def g(a: A, /):
    return {'x': a.x, 'y': a.y, 'z': a}


def h(a: bool, b: uint):
    return {'a': a, 'b': b}


def pid():
    return f'kill {os.getpid()}'


app = Application()
app.add_patch_mapping('.*', pid)
app.add_get_mapping('/complex', f)
app.add_post_mapping('/complex', f)

app.add_get_mapping('/model', g)
app.add_post_mapping('/model', g)

app.add_get_mapping('/other', h)
app.add_post_mapping('/other', h)


app.add_json_bridge(dump_complex)


if __name__ == '__main__':
    app.run()
