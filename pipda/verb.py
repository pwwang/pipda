"""Provide register_verb to register verbs"""
import ast
from collections import namedtuple
from functools import singledispatch, wraps
from types import FunctionType
from typing import Any, Callable, ClassVar, Iterable, Optional, Type, Union

from .utils import NULL, calling_env, have_expr, singledispatch_register
from .function import Function
from .context import ContextBase, Context

# The Sign tuple
Sign = namedtuple('Sign', ['method', 'token'])

# All supported signs
#   method is used to be attached to verbs
#   ast token class is used to check if the verb or function
#       is running in piping mode
PIPING_SIGNS = {
    '+': Sign('__radd__', ast.Add),
    '-': Sign('__rsub__', ast.Sub),
    '*': Sign('__rmul__', ast.Mult),
    '@': Sign('__rmatmul__', ast.MatMult),
    '/': Sign('__rtruediv__', ast.Div),
    '//': Sign('__rfloordiv__', ast.FloorDiv),
    '%': Sign('__rmod__', ast.Mod),
    '**': Sign('__rpow__', ast.Pow),
    '<<': Sign('__rlshift__', ast.LShift),
    '>>': Sign('__rrshift__', ast.RShift),
    '&': Sign('__rand__', ast.BitAnd),
    '^': Sign('__rxor__', ast.BitXor),
    '|': Sign('__ror__', ast.BitOr)
}

class Verb(Function):
    """The verb class"""
    CURRENT_SIGN: ClassVar[str] = None

def register_piping_sign(sign: str):
    """Register a piping sign for the verbs"""
    if sign not in PIPING_SIGNS:
        raise ValueError(f"Unsupported piping sign: {sign}")

    if Verb.CURRENT_SIGN:
        current_sign = PIPING_SIGNS[Verb.CURRENT_SIGN]
        delattr(Verb, current_sign.method)

    Verb.CURRENT_SIGN = sign
    new_sign = PIPING_SIGNS[sign]
    setattr(Verb, new_sign.method, Verb.evaluate)

register_piping_sign('>>')

def register_verb(
        cls: Union[FunctionType, Type, Iterable[Type]] = object,
        context: Union[Context, ContextBase] = NULL,
        func: Optional[FunctionType] = None
) -> Callable:
    """Mimic the singledispatch function to implement a function for
    specific types"""
    if func is None and isinstance(cls, FunctionType):
        func, cls = cls, object
    if func is None:
        return lambda fun: register_verb(cls, context, fun)

    if not isinstance(cls, (tuple, set, list)):
        cls = (cls, )

    if context is NULL:
        context = register_verb.default_context

    if isinstance(context, Context):
        context = context.value

    # allow register to have different context
    func.context = context
    @singledispatch
    @wraps(func)
    def generic(_data: Any, *args: Any, **kwargs: Any) -> Any:
        if object in cls:
            return func(_data, *args, **kwargs)
        raise NotImplementedError(
            f'{func.__name__!r} not registered '
            f'for type: {type(_data)}.'
        )

    for single_cls in cls:
        if single_cls is not object:
            generic.register(single_cls, func)

    @wraps(func)
    def wrapper(
            *args: Any,
            _env: Optional[str] = None,
            **kwargs: Any
    ) -> Any:
        _env = _env or calling_env()
        if isinstance(_env, str) and _env == 'piping-verb':
            return Verb(generic, context, args, kwargs)

        # I am an argument of a verb
        if isinstance(_env, str) and _env == 'piping':
            # Use the verb's context
            return Function(generic, None, args, kwargs, False)

        # otherwise I am standalone
        # If I have Expression objects as arguments, treat it as a Verb
        # and execute it, with the first argument as data
        if have_expr(args[1:], kwargs):
            return Function(
                generic,
                context,
                args[1:],
                kwargs
            ).evaluate(args[0])

        if _env is None:
            return generic(*args, **kwargs)

        # it's context data
        return Verb(generic, context, args, kwargs).evaluate(_env)

    wrapper.register = singledispatch_register(generic.register)
    wrapper.registry = generic.registry
    wrapper.dispatch = generic.dispatch
    wrapper.__pipda__ = 'Verb'
    wrapper.__origfunc__ = func

    return wrapper

register_verb.default_context = Context.SELECT
