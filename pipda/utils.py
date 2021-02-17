"""Provide the utilities and abstract classes"""
import sys
import ast
import warnings
from functools import partialmethod, singledispatch, wraps
from types import FunctionType
from typing import Any, Callable, Mapping, Optional, Tuple, Type, Union
from collections import OrderedDict, namedtuple
from enum import Enum
from abc import ABC, abstractmethod

from executing import Source

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

class Context(Enum):
    """The context how the direct SubsetRef objects should be evaluated

    NAME: evaluate as a str
    DATA: evaluate as a subscript (`data[ref]`)
    MIXED: specially for operator. For unary operators (-1, +1, ~1), use UNSET,
        otherwise use DATA
    UNSET: users to evaluate by themselves
    """
    NAME = 1
    DATA = 2
    MIXED = 3
    UNSET = 4

class Expression(ABC):
    """The abstract Expression class

    Args:
        context: The context of for us the evaluate the SubsetRef and Operator
            objects inside this expression. For those two types of objects, it
            will be `None`

    Attributes:
        context: The context
        func: The function

    """
    def __init__(self, context: Optional[Context] = None) -> None:
        self.context = context

    def __hash__(self) -> int:
        return hash(id(self))

    def __getattr__(self, name: str) -> Any:
        from .symbolic import SubsetRef
        return SubsetRef(self, name, 'getattr', Context.DATA)

    def __getitem__(self, item: Any) -> Any:
        from .symbolic import SubsetRef
        return SubsetRef(self, item, 'getitem', Context.DATA)

    def _op_handler(self, op: str, *args: Any, **kwargs: Any) -> "Operator":
        from .operator import Operator
        return Operator.REGISTERED(op, (self, *args), kwargs)

    # Make sure the operators connect all expressions into one
    __add__ = partialmethod(_op_handler, 'add')
    __radd__ = partialmethod(_op_handler, 'radd')
    __sub__ = partialmethod(_op_handler, 'sub')
    __rsub__ = partialmethod(_op_handler, 'rsub')
    __mul__ = partialmethod(_op_handler, 'mul')
    __rmul__ = partialmethod(_op_handler, 'rmul')
    __matmul__ = partialmethod(_op_handler, 'matmul')
    __rmatmul__ = partialmethod(_op_handler, 'rmatmul')
    __truediv__ = partialmethod(_op_handler, 'truediv')
    __rtruediv__ = partialmethod(_op_handler, 'rtruediv')
    __floordiv__ = partialmethod(_op_handler, 'floordiv')
    __rfloordiv__ = partialmethod(_op_handler, 'rfloordiv')
    __mod__ = partialmethod(_op_handler, 'mod')
    __rmod__ = partialmethod(_op_handler, 'rmod')
    __lshift__ = partialmethod(_op_handler, 'lshift')
    __rlshift__ = partialmethod(_op_handler, 'rlshift')
    __rshift__ = partialmethod(_op_handler, 'rshift')
    __rrshift__ = partialmethod(_op_handler, 'rrshift')
    __and__ = partialmethod(_op_handler, 'and_')
    __rand__ = partialmethod(_op_handler, 'rand')
    __xor__ = partialmethod(_op_handler, 'xor')
    __rxor__ = partialmethod(_op_handler, 'rxor')
    __or__ = partialmethod(_op_handler, 'or_')
    __ror__ = partialmethod(_op_handler, 'ror')
    __pow__ = partialmethod(_op_handler, 'pow')
    __rpow__ = partialmethod(_op_handler, 'rpow')
    __contains__ = partialmethod(_op_handler, 'contains')

    __lt__ = partialmethod(_op_handler, 'lt')
    __le__ = partialmethod(_op_handler, 'le')
    __eq__ = partialmethod(_op_handler, 'eq')
    __ne__ = partialmethod(_op_handler, 'ne')
    __gt__ = partialmethod(_op_handler, 'gt')
    __ge__ = partialmethod(_op_handler, 'ge')
    __neg__ = partialmethod(_op_handler, 'neg')
    __pos__ = partialmethod(_op_handler, 'pos')
    __invert__ = partialmethod(_op_handler, 'invert')

    @abstractmethod
    def evaluate(self, data: Any, context: Context = Context.UNSET) -> Any:
        """Evaluate the expression using given data"""

class Predicate(Expression, ABC):
    """The Predicate class, defining how the function should be executed
    when needed

    Args:
        func: The function to execute
        context: The context to evaluate the SubsetRef/Operator objects

    Attributes:
        func: The function
        context: The context
        args: The arguments of the function
        kwargs: The keyword arguments of the function
    """

    def __init__(self, func: Callable, context: Context):
        super().__init__(context)
        self.func = func
        self.args = self.kwargs = None

    def defer(self, args: Tuple[Any], kwargs: Tuple[Any]):
        """Defer the evaluation when the data is not piped in"""
        self.args = args
        self.kwargs = kwargs
        return self

    def evaluate(self, data: Any, context: Context = Context.UNSET) -> Any:
        """Execute the function with the data and context"""
        if self.context == Context.UNSET:
            # leave args/kwargs for the verb/function/operator to evaluate
            return self.func(data, *self.args, **self.kwargs)

        args = evaluate_args(self.args, data, self.context)
        kwargs = evaluate_kwargs(self.kwargs, data, self.context)
        return self.func(data, *args, **kwargs)

def get_verb_node() -> Tuple[ast.Call, Optional[ast.Call]]:
    """Get the ast node that is ensured the piped verb call"""
    # frame 1: is_piping
    # frame 2: register_verb/register_function.wrapper
    # frame 3: data >> verb(func())
    frame = sys._getframe(3)

    node = Source.executing(frame).node
    if not node:
        raise RuntimeError(
            "Failed to fetch the node where the function is called. "
            "Did you run pipda not in a normal environment?"
        )

    from .verb import Verb
    # check if we have the piping node (i.e. >>)
    child = node
    parent = getattr(node, 'parent', None)
    while parent:
        if (
                isinstance(parent, ast.BinOp) and
                isinstance(parent.op,
                           PIPING_SIGNS[Verb.CURRENT_SIGN].token) and
                parent.right is child
        ):
            return node, child
        child = parent
        parent = getattr(parent, 'parent', None)
    return node, None

def is_argument_node(sub_node: ast.Call,
                     verb_node: Optional[ast.Call]) -> bool:
    """Check if node func() is an argument of verb() (i.e. verb(func()))"""
    if not verb_node:
        return False
    parent = sub_node
    while parent:
        if isinstance(parent, ast.Call) and (
                parent is verb_node or
                parent in verb_node.args or any(
                    keyword.value is sub_node
                    for keyword in verb_node.keywords
                )
        ):
            return True
        parent = getattr(parent, 'parent', None)
    # when verb_node is ensured, we can anyway retrieve it as the parent of
    # sub_node
    return False # pragma: no cover

def is_piping():
    """Check if calling is happening in piping environment"""
    try:
        my_node, verb_node = get_verb_node()
    except RuntimeError:
        warnings.warn(
            "Failed to fetch the node calling the function, "
            "call it with the original function."
        )
        return False
    else:
        return is_argument_node(my_node, verb_node)

def evaluate_expr(
        expr: Any,
        data: Any,
        context: Context,
        callback: Optional[Callable[[Expression], None]] = None
) -> Any:
    """Evaluate a mixed expression"""
    if isinstance(expr, list):
        return [evaluate_expr(elem, data, context) for elem in expr]
    if isinstance(expr, tuple):
        return tuple(evaluate_expr(elem, data, context) for elem in expr)
    if isinstance(expr, set):
        return set(evaluate_expr(elem, data, context) for elem in expr)
    if isinstance(expr, OrderedDict):
        return OrderedDict([
            (key, evaluate_expr(val, data, context))
            for key, val in expr.items()
        ])
    if isinstance(expr, dict):
        return {
            key: evaluate_expr(val, data, context)
            for key, val in expr.items()
        }
    if isinstance(expr, Expression):
        # use its own context, unless it's SubsetRef
        ret = (expr.evaluate(data, context)
               if expr.context is Context.UNSET
               else expr.evaluate(data))
        if callable(callback):
            callback(expr)
        return ret
    return expr

def evaluate_args(
        args: Tuple[Any],
        data: Any,
        context: Context,
        callback: Optional[Callable[[Expression], None]] = None
) -> Tuple[Any]:
    """Evaluate the non-keyword arguments"""
    return tuple(evaluate_expr(arg, data, context, callback) for arg in args)

def evaluate_kwargs(
        kwargs: Mapping[str, Any],
        data: Any,
        context: Context,
        callback: Optional[Callable[[Expression], None]] = None
) -> Mapping[str, Any]:
    """Evaluate the keyword arguments"""
    return {
        key: evaluate_expr(val, data, context, callback)
        for key, val in kwargs.items()
    }

def register_factory(predicate_class: Type[Predicate]) -> Callable:
    """The factory to generate verb/function register decorators"""
    def register_wrapper(
            cls: Optional[Union[FunctionType, Type]] = None,
            context: Context = Context.DATA,
            func: Optional[FunctionType] = None
    ) -> Callable:
        """Mimic the singledispatch function to implement a function for
        specific types"""
        if func is None and isinstance(cls, FunctionType):
            func, cls = cls, None
        if func is None:
            return lambda fun: register_wrapper(cls, context, fun)

        @singledispatch
        def generic(_data: Any, *args: Any, **kwargs: Any) -> Any:
            if not cls:
                return func(_data, *args, **kwargs)
            raise NotImplementedError(
                f'{func.__name__!r} not registered '
                f'for type: {type(_data)}.'
            )

        if cls:
            generic.register(cls, func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            force_piping = kwargs.pop('_force_piping', False)
            if force_piping or is_piping():
                predicate = predicate_class(generic, context)
                return predicate.defer(args, kwargs)
            return func(*args, **kwargs)

        wrapper.register = generic.register
        wrapper.__pipda__ = predicate_class.__name__
        return wrapper
    return register_wrapper
