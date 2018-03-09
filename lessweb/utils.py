def eafp(ask, default):
    """
    Easier to ask for forgiveness than permission
    `x = eafp(lambda: int('a'), 0)` is equivalent to `x = int('a') ?? 0`
    """
    try:
        return ask()
    except:
        return default


class SugarNil:
    def __bool__(self):
        return False


_nil = SugarNil()
