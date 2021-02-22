"""Provide the Operator class"""
from functools import wraps
import operator
from types import MethodType
from pipda.context import Context, ContextBase, ContextEval
from typing import Any, Callable, Mapping, Optional, Tuple, Type, Union

from .function import Function

class Operator(Function):
    """Operator class, defining how the operators in verb/function arguments
    should be evaluated

    Args:
        op: The operator
        args: The arguments of the operator
        kwargs: The keyword arguments of the operator
    """
    REGISTERED = None

    def __init__(self,
                 op: str,
                 context: ContextBase,
                 args: Tuple[Any],
                 kwargs: Mapping[str, Any],
                 datarg: bool = False) -> None:
        self.op = op
        self.data = None
        op_func = getattr(self, self.op)
        super().__init__(op_func, context, args, kwargs, datarg)

    def evaluate(
            self,
            data: Any,
            context: Optional[ContextBase] = None
    ) -> Any:
        """Evaluate the operator

        No data passed to the operator function. It should be used to evaluate
        the arguments.
        """
        self.context = context
        self.data = data
        return super().evaluate(data, context)

    def __getattr__(self, name: str) -> Any:
        op_func = getattr(operator, name, None)
        if not op_func and name.startswith('r'):
            op_func = getattr(operator, name[1:], None)
            if op_func:
                @wraps(op_func)
                def _(a, b, *args, **kwargs):
                    return op_func(b, a, *args, **kwargs)
        if op_func is None:
            raise ValueError(f'Cannot find the operator {name!r}, '
                             'have you define it in your operator class?')
        return op_func

def register_operator(op_class: Type[Operator]) -> Type[Operator]:
    """Register an Operator class

    The context count be a dict of operator name to context.
    For those operators not listed, will use Context.EVAL.
    """
    if not issubclass(op_class, Operator):
        raise ValueError(
            "The operator class to be registered must be "
            "a subclass of pipda.Operator."
        )
    Operator.REGISTERED = op_class
    return op_class

register_operator(Operator)
