"""Provide register_verb to register verbs"""
import ast
from collections import namedtuple
from functools import singledispatch, wraps
from types import FunctionType
from typing import Any, Callable, ClassVar, Iterable, Optional, Type, Union

from .utils import is_piping
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
        context: Union[Context, ContextBase] = Context.SELECT,
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

    if isinstance(context, Context):
        context = context.value

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
    def wrapper(*args: Any,
                _force_piping: bool = False,
                **kwargs: Any) -> Any:
        if _force_piping or is_piping():
            return Verb(generic, context, args, kwargs)

        return func(*args, **kwargs)

    wrapper.register = generic.register
    wrapper.registry = generic.registry
    wrapper.dispatch = generic.dispatch
    wrapper.__pipda__ = 'Verb'

    return wrapper
