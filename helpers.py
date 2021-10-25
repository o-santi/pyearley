class reprwrapper(object):
    def __init__(self, repr, func):
        self._repr = repr
        self._func = func
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kw):
        return self._func(*args, **kw)

    def __repr__(self):
        return self._repr(self._func)


# just a wrapper to change __repr__ of lambda functions
def withrepr(reprfun):
    def _wrap(func):
        return reprwrapper(reprfun, func)

    return _wrap


def dump_args(func):
    """
    Decorator to print function call details.

    This includes parameters names and effective values.
    """

    def wrapper(*args, **kwargs):
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ", ".join(map("{0[0]} = {0[1]!r}".format, func_args.items()))
        print(f"{func.__module__}.{func.__qualname__} ( {func_args_str} )")
        return func(*args, **kwargs)

    return wrapper


def chars(string: str):
    @withrepr(lambda x: f"[{string}]" if len(string) > 1 else string)
    def func(x: str):
        return x in string and len(x) > 0

    return func


def range_number(num: str):
    @withrepr(lambda x: f"[{num}]")
    def func(x: str):
        if not x.isnumeric():
            return False
        return int(num[0]) < int(x) < int(num[1])

    return func
