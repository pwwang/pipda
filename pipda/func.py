"""Provide register_func function"""
import sys
from types import FunctionType
from functools import wraps, singledispatch
from executing import Source

from .symbolic import Symbolic

class Func(Symbolic):
    """Symbolic for functions"""
    def __init__(self, exet):
        super().__init__(Symbolic._NAME__, exet)

def register_func(cls=None, func=None):
    """Register a function used in Verb arguments"""
    if func is None and isinstance(cls, FunctionType):
        func, cls = cls, None
    if func is None:
        return lambda fun: register_func(cls, fun)

    @singledispatch
    def generic(_data, _context, *args, **kwargs):
        if not cls:
            return func(_data, _context, *args, **kwargs)
        raise NotImplementedError(f'Function {func.__name__!r} not registered '
                                  f'for type: {type(_data)}.')

    if cls:
        generic.register(cls, func)

    @wraps(func)
    def wrapper(*args, **kwargs): # pylint: disable=unused-argument
        exet = Source.executing(sys._getframe(1))
        return Func(exet)

    wrapper.pipda = generic
    wrapper.register = generic.register
    return wrapper
