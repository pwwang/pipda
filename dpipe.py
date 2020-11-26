"""A framework for data piping in python"""
import sys
import ast
from functools import wraps

import executing
from varname import varname

# pylint: disable=unused-argument,eval-used

def get_node():
    """Get the node of the symbolic"""
    return executing.Source.executing(sys._getframe(2)).node

class Symbolic:
    """A symbolic representation to make X.a and alike valid python syntaxes"""

    def __init__(self, name=None, node=None):
        # X itself is a node
        self.name = name or varname()
        self.node = node or ast.Name(id=self.name, ctx=ast.Load())

    def _any_args(self, *args, **kwargs):
        return Symbolic(self.name, get_node())

    def _no_args(self):
        return Symbolic(self.name, get_node())

    def _single_arg(self, arg):
        return Symbolic(self.name, get_node())

    __call__ = _any_args

    __getitem__ = __getattr__ = __contains__ = _single_arg

    __add__ = _single_arg
    __sub__ = _single_arg
    __mul__ = _single_arg
    __matmul__ = _single_arg
    __truediv__ = _single_arg
    __floordiv__ = _single_arg
    __mod__ = _single_arg
    __divmod__ = _single_arg
    __pow__ = _any_args
    __lshift__ = _single_arg
    __rshift__ = _single_arg
    __and__ = _single_arg
    __xor__ = _single_arg
    __or__ = _single_arg

    __radd__ = _single_arg
    __rsub__ = _single_arg
    __rmul__ = _single_arg
    __rmatmul__ = _single_arg
    __rtruediv__ = _single_arg
    __rfloordiv__ = _single_arg
    __rmod__ = _single_arg
    __rdivmod__ = _single_arg
    __rpow__ = _any_args
    __rlshift__ = _single_arg
    __rrshift__ = _single_arg
    __rand__ = _single_arg
    __rxor__ = _single_arg
    __ror__ = _single_arg

    __lt__ = _single_arg
    __le__ = _single_arg
    __eq__ = _single_arg
    __ne__ = _single_arg
    __gt__ = _single_arg
    __ge__ = _single_arg

    __len__ = __reversed__ = _no_args

    @property
    def eval_(self):
        """Convert the symbolic representation into a callable"""
        print(ast.dump(self.node))
        lambd_node = ast.Expression(
            body=ast.Lambda(
                ast.arguments(posonlyargs=[],
                              args=[ast.arg(arg=self.name)],
                              kwonlyargs=[],
                              kw_defaults=[],
                              defaults=[]),
                body=self.node
            )
        )
        ast.fix_missing_locations(lambd_node)
        code = compile(lambd_node, filename='<dpipe-ast>', mode='eval')

        return eval(code)

class Piped:
    """A wrapper for the verbs"""
    def __init__(self, cls, func, args, kwargs):
        self.cls = cls
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def eval_args(self, data):
        """Evaluate the args"""
        return (arg.eval_(data) if isinstance(arg, Symbolic) else arg
                for arg in self.args)

    def eval_kwargs(self, data):
        """Evaluate the kwargs"""
        return {key: (val.eval_(data) if isinstance(val, Symbolic) else val)
                for key, val in self.kwargs.items()}

    def __rrshift__(self, data):
        if not isinstance(data, self.cls):
            raise TypeError(f"{type(data)} is not registered for data piping.")
        return self.func(data, *self.eval_args(data), **self.eval_kwargs(data))

def single_dispatch(cls, func=None):
    """Mimic the singledispatch function to implement a function for
    specific types"""
    if func is None:
        return lambda fun: single_dispatch(cls, fun)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return Piped(cls, func, args, kwargs)

    return wrapper
