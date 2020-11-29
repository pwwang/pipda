"""Provide register_func function"""
import sys
from types import FunctionType
from functools import wraps
from executing import Source

from .symbolic import Symbolic

class Func(Symbolic):
    """Symbolic for functions"""
    def __init__(self, exet):
        super().__init__(Symbolic.NAME, exet)

def register_func(types=None, func=None):
    """Register a function used in Verb arguments"""
    if func is None and isinstance(types, FunctionType):
        func, types = types, None
    if func is None:
        return lambda fun: register_func(types, fun)

    @wraps(func)
    def wrapper(*args, **kwargs): # pylint: disable=unused-argument
        exet = Source.executing(sys._getframe(1))
        return Func(exet)

    @wraps(func)
    def func_with_typecheck(*args, **kwargs):
        if types and not isinstance(args[0], types):
            raise TypeError(f'{func.__name__} is not registered '
                            f'for {type(args[0]).__name__}.')
        return func(*args, **kwargs)
    wrapper.pipda = func_with_typecheck
    return wrapper
