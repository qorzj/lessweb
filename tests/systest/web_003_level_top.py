import os
from lessweb import Application, Context, ResponseStatus, ParamStr, MultipartFile, Model


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


def g(x: Model[A]):
    a = x.get()
    return {'x': a.x, 'y': a.y, 'z': a, 'X': x}


def pid():
    return f'kill {os.getpid()}'


app = Application(encoding='gb2312')
app.add_patch_mapping('.*', pid)
app.add_get_mapping('/complex', f)
app.add_get_mapping('/model', g)

app.add_request_bridge(load_complex)
app.add_response_bridge(dump_complex)


if __name__ == '__main__':
    app.run()
