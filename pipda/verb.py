"""Provide Verb class and register_verb function"""
from functools import wraps
from .symbolic import Symbolic

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

    def __rrshift__(self, data):
        if not isinstance(data, self.types):
            raise TypeError(f"{type(data)} is not registered for data piping.")
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
