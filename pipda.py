"""A framework for data piping in python"""
import sys
import ast
from copy import deepcopy
from functools import wraps

from executing import Source
from varname import varname

# pylint: disable=unused-argument,eval-used
class Transformer(ast.NodeTransformer):
    """Transform a call into the real call"""
    def __init__(self, name):
        self.name = name

    def visit_Call(self, node): # pylint: disable=invalid-name
        """Get the real calls"""
        node.args.insert(0, ast.Name(id=self.name, ctx=ast.Load()))
        ret = ast.Call(
            func=ast.Attribute(value=node.func,
                               attr='__pipda__',
                               ctx=ast.Load()),
            args=node.args,
            keywords=node.keywords
        )
        return ret

class Symbolic:
    """A symbolic representation to make X.a and alike valid python syntaxes"""
    NAME = None

    def __init__(self, name=None, exet=None):
        self.name = name or varname(raise_exc=False) or self.__class__.NAME
        if not self.__class__.NAME:
            self.__class__.NAME = self.name
        if self.__class__.NAME != self.name:
            raise ValueError('Only one Symbolic object is allowed.')
        self.exet = exet

    def __repr__(self) -> str:
        if not self.exet:
            return f'<{self.__class__.__name__}:{self.name}>'
        return (f'<{self.__class__.__name__}:{self.name} ' # pragma: no cover
                f'({ast.dump(self.exet.node)})>')

    def _any_args(self, *args, **kwargs):
        return Symbolic(self.name, Source.executing(sys._getframe(1)))

    # def _no_args(self):
    #     return Symbolic(self.name, Source.executing(sys._getframe(1)))

    def _single_arg(self, arg):
        return Symbolic(self.name, Source.executing(sys._getframe(1)))

    __call__ = _any_args
    __getitem__ = __getattr__ = __contains__ = _single_arg

    __add__ = __sub__ = __mul__ = __matmul__ = __truediv__ = _single_arg
    __floordiv__ = __mod__ = __divmod__ = __lshift__ = _single_arg
    __rshift__ = __and__ = __xor__ = __or__ = _single_arg
    __pow__ = _any_args

    __radd__ = __rsub__ = __rmul__ = __rmatmul__ = __rtruediv__ = _single_arg
    __rfloordiv__ = __rmod__ = __rdivmod__ = __rlshift__ = _single_arg
    __rrshift__ = __rand__ = __rxor__ = __ror__ = _single_arg
    __rpow__ = _any_args

    __lt__ = __le__ = __eq__ = _single_arg
    __ne__ = __gt__ = __ge__ = _single_arg

    # __len__ = __reversed__ = _no_args

    @property
    def eval_(self):
        """Convert the symbolic representation into a callable"""

        lambd_node = ast.Expression(
            # see https://github.com/alexmojaki/executing/issues/17
            Transformer(self.name).visit(deepcopy(self.exet.node))
            if self.exet
            else ast.Name(id=self.name, ctx=ast.Load())
        )
        ast.fix_missing_locations(lambd_node)
        code = compile(lambd_node, filename='<pipda-ast>', mode='eval')
        if not self.exet:
            globs = locs = globals()
        else:
            globs = self.exet.frame.f_globals
            locs = self.exet.frame.f_locals
        return lambda data: eval(code, globs, {**locs, self.name: data})

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

def register_func(func=None):
    """Register a function used in Piped arguments"""
    if func is None:
        return register_func

    @wraps(func)
    def wrapper(*args, **kwargs):
        exet = Source.executing(sys._getframe(1))
        return Symbolic(None, exet)
    wrapper.__pipda__ = func
    return wrapper

def single_dispatch(cls, func=None):
    """Mimic the singledispatch function to implement a function for
    specific types"""
    if func is None:
        return lambda fun: single_dispatch(cls, fun)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return Piped(cls, func, args, kwargs)

    return wrapper
