"""Provide Verb class and register_verb function"""
from abc import ABC, abstractmethod
from functools import wraps, singledispatch
from types import FunctionType

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

class ProxyCompiler(ABC):
    """Defining how to compile a proxy (X.a)"""
    def __init__(self, data):
        self.data = data

    @abstractmethod
    def __getattr__(self, name):
        ... # pragma: no cover

class ProxyCompilerData(ProxyCompiler):
    """Compile X.a to getattr(X, 'a')"""
    def __getattr__(self, name):
        return getattr(self.data, name)

class ProxyCompilerName(ProxyCompiler):
    """Compile X.a to 'a'"""
    def __getattr__(self, name):
        return name

def proxy_compiler_factory(compile_proxy):
    """Generate a ProxyCompiler class"""
    if compile_proxy == 'data':
        return ProxyCompilerData

    if compile_proxy == 'name':
        return ProxyCompilerName

    if callable(compile_proxy):
        class ProxyCompilerCustom(ProxyCompiler):
            """Custom proxy compiler"""
            def __getattr__(self, name):
                return compile_proxy(self.data, name)

        return ProxyCompilerCustom

    raise ValueError(f"Cannot compile proxy with {compile_proxy!r}, "
                     "expected 'data', 'name' or callable.")

class VerbArg:
    """A class to wrap the verb argument,
    which the argument will be compiled to if compile_proxy is None"""

    def __init__(self, data, compile_func):
        self.data = data
        self.compile_func = compile_func

    def set_data(self, data):
        """Set the base data of the argument"""
        self.data = data
        return self

    def compile_to(self, compile_proxy):
        """Compile the argument by given proxy compiling strategy"""
        return self.compile_func(
            self.data,
            proxy_compiler_factory(compile_proxy)
        )

class Verb:
    """A wrapper for the verbs"""

    def __init__(self, func, args, kwargs, compile_proxy):
        self.compile_proxy = compile_proxy
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def _eval_single_arg(self, arg, data):
        if not isinstance(arg, Symbolic):
            return arg

        verb_arg = VerbArg(data, arg.eval_)
        if self.compile_proxy:
            return verb_arg.compile_to(self.compile_proxy)
        return verb_arg

    def eval_args(self, data):
        """Evaluate the args"""
        return (self._eval_single_arg(arg, data)
                for arg in self.args)

    def eval_kwargs(self, data):
        """Evaluate the kwargs"""
        return {key: self._eval_single_arg(val, data)
                for key, val in self.kwargs.items()}

    def _sign(self, data):
        return self.func(data, *self.eval_args(data), **self.eval_kwargs(data))

def register_verb(cls=None, compile_proxy='data', func=None):
    """Mimic the singledispatch function to implement a function for
    specific types"""
    if func is None and isinstance(cls, FunctionType):
        func, cls = cls, None
    if func is None:
        return lambda fun: register_verb(cls, compile_proxy, fun)

    @singledispatch
    def generic(_data, *args, **kwargs):
        if not cls:
            return func(_data, *args, **kwargs)
        raise NotImplementedError(f'Verb {func.__name__!r} not registered '
                                  f'for type: {type(_data)}.')

    if cls:
        generic.register(cls, func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return Verb(generic, args, kwargs, compile_proxy)

    wrapper.pipda = generic
    wrapper.register = generic.register

    return wrapper

def piping_sign(sign):
    """Define the piping sign"""
    if sign not in SIGN_MAPPING:
        raise ValueError(f'Unsupported sign: {sign}, '
                         f'expected {list(SIGN_MAPPING)}')
    setattr(Verb, SIGN_MAPPING[sign], Verb._sign)

piping_sign('>>')
