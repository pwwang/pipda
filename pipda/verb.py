"""Provide Verb class and register_verb function"""
from functools import wraps
from .symbolic import Symbolic

SIGN_MAPPING = {
    '+': '__radd__',
    '-': '__rsub__',
    '*': '__rmul__',
    '@': '__rmatmul__',
    '/': '__rtruediv__',
    '//': '__rfloordiv__',
    '%': '__rmod__',
    '**': '__rpow__',
    '<<': '__rlshift__',
    '>>': '__rrshift__',
    '&': '__rand__',
    '^': '__rxor__',
    '|': '__ror__',
}

class Verb:
    """A wrapper for the verbs"""

    def __init__(self, types, compile_attrs, func, args, kwargs):
        self.types = types
        self.compile_attrs = compile_attrs
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def eval_args(self, data):
        """Evaluate the args"""
        return (arg.eval_(self.compile_attrs)(data)
                if isinstance(arg, Symbolic) else arg
                for arg in self.args)

    def eval_kwargs(self, data):
        """Evaluate the kwargs"""
        return {key: (val.eval_(self.compile_attrs)(data)
                      if isinstance(val, Symbolic) else val)
                for key, val in self.kwargs.items()}

    def _sign(self, data):
        if not isinstance(data, self.types):
            raise TypeError(f"{type(data)} is not registered for data piping "
                            f"with function: {self.func.__name__}.")
        return self.func(data, *self.eval_args(data), **self.eval_kwargs(data))


def register_verb(types, compile_attrs=True, func=None):
    """Mimic the singledispatch function to implement a function for
    specific types"""
    if func is None:
        return lambda fun: register_verb(types, compile_attrs, fun)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return Verb(types, compile_attrs, func, args, kwargs)

    wrapper.pipda = func
    return wrapper

def piping_sign(sign):
    """Define the piping sign"""
    if sign not in SIGN_MAPPING:
        raise ValueError(f'Unsupported sign: {sign}, '
                         f'expected {list(SIGN_MAPPING)}')
    setattr(Verb, SIGN_MAPPING[sign], Verb._sign)

piping_sign('>>')
