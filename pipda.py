"""A framework for data piping in python"""
import sys
import ast
from copy import deepcopy
from functools import wraps

from executing import Source
from varname import varname

__version__ = '0.0.1'

# pylint: disable=unused-argument,eval-used
class Transformer(ast.NodeTransformer):
    """Transform a call into the real call"""
    # pylint: disable=invalid-name
    def __init__(self, name, compile_attrs):
        self.name = name
        self.compile_attrs = compile_attrs

    def visit_Attribute(self, node):
        """If compile_attrs is False, just turn X.a into 'a'"""
        try:
            if self.compile_attrs or node.value.id != self.name:
                return node
        except AttributeError: # node.value is not ast.Name
            return node

        return ast.Str(node.attr)

    def visit_Call(self, node):
        """Get the real calls"""
        node.args.insert(0, ast.Name(id=self.name, ctx=ast.Load()))
        return ast.Call(
            func=ast.Attribute(value=self.visit(node.func),
                               attr='__pipda__',
                               ctx=ast.Load()),
            args=[self.visit(arg) for arg in node.args],
            keywords=[self.visit(kwarg) for kwarg in node.keywords]
        )

    def visit_UnaryOp(self, node):
        """Make -X.x available"""
        return self.visit(ast.Call(
            func=ast.Name(
                id=('__neg__' if isinstance(node.op, ast.USub)
                    else '__pos__' if isinstance(node.op, ast.UAdd)
                    else '__invert__' if isinstance(node.op, ast.Invert)
                    else 'UnsupportedUnaryOp'),
                ctx=ast.Load()
            ),
            args=[node.operand],
            keywords=[]
        ))

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

    def _no_args(self):
        return Symbolic(self.name, Source.executing(sys._getframe(1)))

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

    __neg__ = __pos__ = __invert__ = _no_args

    def eval_(self, compile_attrs=True):
        """Convert the symbolic representation into a callable"""
        lambody = ast.Expression(
            # see https://github.com/alexmojaki/executing/issues/17
            Transformer(self.name, compile_attrs).visit(
                deepcopy(self.exet.node)
            )
            if self.exet
            else ast.Name(id=self.name, ctx=ast.Load())
        )
        ast.fix_missing_locations(lambody)
        code = compile(lambody, filename='<pipda-ast>', mode='eval')
        if not self.exet:
            globs = locs = globals()
        else:
            globs = self.exet.frame.f_globals
            locs = self.exet.frame.f_locals
        def func(data):
            body = eval(code, globs, {**locs, self.name: data})
            return body
        return func

class Piped:
    """A wrapper for the verbs"""
    def __init__(self, cls, compile_attrs, func, args, kwargs):
        self.cls = cls
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

def single_dispatch(cls, compile_attrs=True, func=None):
    """Mimic the singledispatch function to implement a function for
    specific types"""
    if func is None:
        return lambda fun: single_dispatch(cls, compile_attrs, fun)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return Piped(cls, compile_attrs, func, args, kwargs)

    wrapper.__pipda__ = func
    return wrapper
