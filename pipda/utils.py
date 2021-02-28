"""Provide the utilities and Expression class"""
import sys
import ast
import warnings
from functools import partialmethod
from typing import Any, Mapping, Optional, Tuple, Union
from abc import ABC, abstractmethod

from executing import Source

NULL = object()

class Expression(ABC):
    """The abstract Expression class

    Args:
        context: The context for evaluation.
    """
    def __init__(self, context: Optional["ContextBase"] = None) -> None:
        self.context = context

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
        return Operator.REGISTERED(op, None, (self, *args), kwargs)

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

    def __index__(self): # pylint: disable=invalid-index-returned
        """Allow Expression object to work as indexes"""
        return None

    @abstractmethod
    def evaluate(
            self,
            data: Any,
            context: Optional["ContextBase"] = None
    ) -> Any:
        """Evaluate the expression using given data"""


def get_verb_node() -> Tuple[ast.Call, Optional[ast.Call]]:
    """Get the ast node that is ensured the piped verb call"""
    # frame 1: is_piping
    # frame 2: register_verb/register_func.wrapper
    # frame 3: data >> verb(func())
    from .verb import PIPING_SIGNS
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
        context: Union["Context", "ContextBase"]
) -> Any:
    """Evaluate a mixed expression"""
    from .context import Context
    if isinstance(context, Context):
        context = context.value

    if isinstance(expr, list):
        return [evaluate_expr(elem, data, context) for elem in expr]
    if isinstance(expr, tuple):
        return tuple(evaluate_expr(elem, data, context) for elem in expr)
    if isinstance(expr, set):
        return set(evaluate_expr(elem, data, context) for elem in expr)
    if isinstance(expr, slice):
        return slice(
            evaluate_expr(expr.start, data, context),
            evaluate_expr(expr.stop, data, context),
            evaluate_expr(expr.step, data, context)
        )
    # no need anymore for python3.7+
    # if isinstance(expr, OrderedDict):
    #     return OrderedDict([
    #         (key, evaluate_expr(val, data, context))
    #         for key, val in expr.items()
    #     ])
    if isinstance(expr, dict):
        return {
            key: evaluate_expr(val, data, context)
            for key, val in expr.items()
        }
    if isinstance(expr, Expression):
        # use its own context, unless it's a Reference or Operator object
        ret = (expr.evaluate(data, context)
               if not expr.context
               else expr.evaluate(data))
        return ret
    return expr

def evaluate_args(
        args: Tuple[Any],
        data: Any,
        context: Union["Context", "ContextBase"]
) -> Tuple[Any]:
    """Evaluate the non-keyword arguments"""
    return tuple(evaluate_expr(arg, data, context) for arg in args)

def evaluate_kwargs(
        kwargs: Mapping[str, Any],
        data: Any,
        context: Union["Context", "ContextBase"]
) -> Mapping[str, Any]:
    """Evaluate the keyword arguments"""
    return {
        key: evaluate_expr(val, data, context)
        for key, val in kwargs.items()
    }
