"""Provide the utilities and Expression class"""
from enum import Enum
import sys
import ast
import logging
from types import FrameType
import warnings
from functools import partialmethod
from typing import (
    Any, Callable, Iterable, Mapping, Optional, Tuple, Type, Union
)
from abc import ABC, abstractmethod

from executing import Source

from .context import ContextAnnoType, ContextBase

NULL = object()
DATA_CONTEXTVAR_NAME = '__pipda_data__'


# logger
logger = logging.getLogger('pipda') # pylint: disable=invalid-name
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler() # pylint: disable=invalid-name
stream_handler.setFormatter(logging.Formatter(
    '[%(asctime)s][%(name)s][%(levelname)7s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger.addHandler(stream_handler)

class Expression(ABC):
    """The abstract Expression class"""

    def __hash__(self) -> int:
        """Make it hashable"""
        return hash(id(self))

    def __getattr__(self, name: str) -> "ReferenceAttr":
        """Whenever `expr.attr` is encountered,
        return a ReferenceAttr object"""
        from .symbolic import ReferenceAttr
        return ReferenceAttr(self, name)

    def __getitem__(self, item: Any) -> "ReferenceItem":
        """Whenever `expr[item]` is encountered,
        return a ReferenceAttr object"""
        from .symbolic import ReferenceItem
        return ReferenceItem(self, item)

    def _op_handler(self, op: str, *args: Any, **kwargs: Any) -> "Operator":
        """Handle the operators"""
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

    # pylint: disable=bad-option-value,invalid-index-returned
    def __index__(self):
        """Allow Expression object to work as indexes"""
        return None

    @abstractmethod
    def __call__(
            self,
            data: Any,
            context: Optional[ContextBase] = None,
            level: int = 0
    ) -> Any:
        """Evaluate the expression using given data"""

class DataEnv:
    """A data context that can be accessed by the function registered by
    `pipda.register_*` so that the data argument doesn't need to
    be passed when called

    Args:
        data: The data to be attached to the context
    """

    def __init__(self, data: Any, name: str = DATA_CONTEXTVAR_NAME) -> None:
        self.name = name
        self.data = data

    def get(self) -> Any:
        """Get the data"""
        return self.data

    def set(self, data: Any) -> None:
        """Update the data"""
        self.data = data

    def delete(self) -> None:
        """Delete the attached data"""
        self.set(None)

def get_verb_node(
        calling_node: ast.Call
) -> Tuple[ast.Call, Optional[ast.Call]]:
    """Get the ast node that is ensured the piped verb call"""
    from .verb import PIPING_SIGNS, Verb
    # check if we have the piping node (i.e. >>)
    child = calling_node
    parent = getattr(child, 'parent', None)
    while parent:
        if (
                (
                    isinstance(parent, ast.BinOp) and parent.right is child or
                    isinstance(parent, ast.AugAssign) and parent.value is child
                ) and
                isinstance(parent.op, PIPING_SIGNS[Verb.CURRENT_SIGN].token)
        ):
            return child

        child = parent
        parent = getattr(parent, 'parent', None)
    return None

def get_env_data(frame: FrameType) -> Any:
    """Check and return if there is a data set in the context where
    the verb or function is called"""
    for value in frame.f_locals.values():
        if not isinstance(value, DataEnv):
            continue
        if value.name != DATA_CONTEXTVAR_NAME:
            continue
        return value.get()
    return None

def is_argument_node(
        sub_node: ast.Call,
        verb_node: Optional[ast.Call]
) -> bool:
    """Check if node func() is an argument of verb() (i.e. verb(func()))"""
    if not verb_node:
        return False
    parent = sub_node
    while parent:
        if isinstance(parent, ast.Call) and (
                parent is verb_node or
                is_argument_node_of(parent) is verb_node
        ):
            return True
        if isinstance(parent, ast.Lambda):
            # function inside lambda is not in a piping environment
            return False
        parent = getattr(parent, 'parent', None)
    # when verb_node is ensured, we can anyway retrieve it as the parent of
    # sub_node
    return False # pragma: no cover

def is_argument_node_of(sub_node: ast.Call) -> Optional[ast.Call]:
    """Check if node func() is an argument of any function calls"""
    parent = getattr(sub_node, 'parent', None)
    while parent:
        if isinstance(parent, ast.Call) and (
                sub_node in parent.args or any(
                    keyword.value is sub_node
                    for keyword in parent.keywords
                )
        ):
            return parent
        if isinstance(parent, ast.Lambda):
            # function inside lambda is not in a piping environment
            return None
        parent = getattr(parent, 'parent', None)
    return None

def calling_env(astnode_fail_warning: bool = True) -> Any:
    """Checking how the function is called:
    - piping:
        1. It is a verb that is piped directed. ie. data >> verb(...)
        2. It is a function called as (part of) the argument of a piping verb.
            ie.:

            >>> data >> verb(func(...))

            Note: `func` here could also be a verb. When a function is called
            inside a lambda body, it should not be counted in this situation:

            >>> data >> verb(lambda: func(...))

            In this case, func should be called as normal function.
            This function should return `None`
    - the context data:
        It is a verb that is not piped but with a data context. ie.:

        >>> data = contextvars.ContextVar(DATA_CONTEXTVAR_NAME, default=data)
        >>> y = verb(arg)

        Note that in such a case, the function should not be called as (part of)
        any arguments of other function calls. If so, this function should
        return `piping`, leaving it for the parent funtion to evaluate it.
    - None:
        None of the above situation fits

    This function should be only called inside register_*.wrapper
    """
    # frame 1: register_*.wrapper
    # frame 2: func(...)
    frame = sys._getframe(2)
    my_node = Source.executing(frame).node
    if not my_node and astnode_fail_warning:
        warnings.warn(
            "Failed to fetch the node calling the function, "
            "call it with the original function."
        )
        return None

    piping_verb_node = get_verb_node(my_node)
    if piping_verb_node is my_node and piping_verb_node is not None:
        return 'piping-verb'

    if is_argument_node(my_node, piping_verb_node):
        return 'piping'

    # get the context data
    contextdata = get_env_data(frame)
    if contextdata is None:
        return None

    if is_argument_node_of(my_node) is not None:
        # When working as an argument, the function is working in piping mode
        # Because we don't know (or it takes too much efforts to) whether
        # the parent node is a function registered by pipda.register_* or not.
        return 'piping'

    return contextdata

def evaluate_expr(
        expr: Any,
        data: Any,
        context: ContextAnnoType,
        level: int = 0
) -> Any:
    """Evaluate a mixed expression"""
    if isinstance(context, Enum):
        context = context.value

    if isinstance(expr, Expression):
        return expr(data, context, level+1)

    if hasattr(expr.__class__, '_pipda_eval'):
        return expr._pipda_eval(data, context, level)

    if isinstance(expr, (tuple, list, set)):
        # In case it's subclass
        return expr.__class__((
            evaluate_expr(elem, data, context, level)
            for elem in expr
        ))
    if isinstance(expr, slice):
        return slice(
            evaluate_expr(expr.start, data, context, level),
            evaluate_expr(expr.stop, data, context, level),
            evaluate_expr(expr.step, data, context, level)
        )
    # no need anymore for python3.7+
    # if isinstance(expr, OrderedDict):
    #     return OrderedDict([
    #         (key, evaluate_expr(val, data, context))
    #         for key, val in expr.items()
    #     ])
    if isinstance(expr, dict):
        return expr.__class__({
            key: evaluate_expr(val, data, context, level)
            for key, val in expr.items()
        })
    return expr

def evaluate_args(
        args: Tuple[Any],
        data: Any,
        context: ContextAnnoType,
        level: int = 0
) -> Tuple[Any]:
    """Evaluate the non-keyword arguments"""
    return tuple(evaluate_expr(arg, data, context, level) for arg in args)

def evaluate_kwargs(
        kwargs: Mapping[str, Any],
        data: Any,
        context: ContextAnnoType,
        level: int = 0
) -> Mapping[str, Any]:
    """Evaluate the keyword arguments"""
    return {
        key: evaluate_expr(val, data, context, level)
        for key, val in kwargs.items()
    }

def singledispatch_register(
        register: Callable[[Type, Callable], Callable]
) -> Callable[
        [Union[Type, Iterable[Type]], Any, Optional[Callable]],
        Callable
]:
    """Allow register of generic function to register types with context"""

    def register_func(
            cls: Union[Type, Iterable[Type]],
            context: Any = None,
            func: Optional[Callable] = None
    ) -> Callable:
        if not isinstance(cls, (tuple, set, list)):
            cls = [cls]

        if func is None:
            return lambda fun: register_func(cls, context, fun)
        if isinstance(context, Enum):
            context = context.value
        func.context = context
        ret = func
        for klass in cls:
            ret = register(klass, ret)
        return ret

    return register_func

def functype(func: Callable) -> str:
    """Check the type of the function

    Args:
        func: A function

    Returns:
        The type of the function
        - verb: A verb that is registered by `register_verb`
        - func: A function that is registered by `register_func`, with
            data as the first argument
        - plain-func: A function that is registered by `register_func`,
            without data as the first argument
        - plain: A plain python function
    """
    pipda_type = getattr(func, '__pipda__', None)
    if pipda_type == 'Verb':
        return 'verb'
    if pipda_type == 'Function':
        return 'func'
    if pipda_type == 'PlainFunction':
        return 'plain-func'
    return 'plain'

def unregister(func: Callable) -> Callable:
    """Get the original function before register

    Args:
        func: The function that is either registered by
            `register_verb` or `register_func`

    Returns:
        The original function that before register
    """
    origfunc = getattr(func, '__origfunc__', None)
    if origfunc is None:
        raise ValueError(f'Function is not registered with pipda: {func}')
    return origfunc

def is_expr(expr: Any) -> bool:
    """Check if an expression includes any Expression object"""
    if isinstance(expr, (list, tuple, set)):
        return any(is_expr(elem) for elem in expr)

    if isinstance(expr, dict):
        return any(is_expr(item) for item in expr.items())

    return isinstance(expr, Expression)

def have_expr(args: Tuple[Any], kwargs: Mapping[str, Any]) -> bool:
    """Check if arg and kwargs have Expression object"""
    for arg in args:
        if is_expr(arg):
            return True
    for arg in kwargs.values():
        if is_expr(arg):
            return True
    return False
