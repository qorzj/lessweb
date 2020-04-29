from enum import Enum
from lessweb import Application, Model


def load_enum(obj, real_type):
    if issubclass(real_type, Enum):
        if isinstance(obj, str) and obj.isdigit():
            return real_type(int(obj))
        else:
            return real_type(obj)


def dump_enum(source):
    if isinstance(source, Enum):
        return {'value': source.value, 'show': source.show} \
            if hasattr(source, 'show') else source.value


class Rank(Enum):
    A = 'A'
    B = 'B'
    C = 'C'


class Gender(Enum):
    MALE = 1
    FEMALE = 2

Gender.MALE.show = '男'
Gender.FEMALE.show = '女'

class User:
    id: int
    gender: Gender
    rank: Rank

def add_user(user: Model[User]):
    return user()

app = Application()
app.add_post_mapping('/user', dealer=add_user)
app.add_json_bridge(dump_enum)
app.run()