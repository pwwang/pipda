"""Provide the Operator class"""
from functools import wraps
import operator
from typing import Any, Mapping, Optional, Tuple, Type

from .function import Function
from .context import ContextBase

class Operator(Function):
    """Operator class, defining how the operators in verb/function arguments
    should be evaluated

    Args:
        op: The operator
        context: Should be None while initialization. It depends on the
            verb or the function that uses it as an argument
        args: The arguments of the operator
        kwargs: The keyword arguments of the operator
        datarg: Should be False. No data argument for the operator function.

    Attributes:
        REGISTERED: The registered Operator class. It's this class by default
            Use `register_operator` as a decorator to register a operator class
    """
    REGISTERED = None

    def __init__(self,
                 op: str,
                 context: Optional[ContextBase],
                 args: Tuple[Any],
                 kwargs: Mapping[str, Any],
                 datarg: bool = False) -> None:

        assert context is None, (
            "No context should be passed "
            f"when initialize a {self.__class__.__name__} object."
        )
        self.op = op
        self.data = None
        # if the function is defined directly, use it.
        # otherwise, get one from `__getattr__`
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
        assert context is not None, (
            "A context is needed to evaluate "
            f"a {self.__class__.__name__} object"
        )
        # set the context and data in case they need to be used
        # inside the function.
        self.context = context
        self.data = data
        return super().evaluate(data, context)

    def __getattr__(self, name: str) -> Any:
        """Get the function to handle the operator"""
        # See if standard operator function exists
        op_func = getattr(operator, name, None)
        # If not, and it's right version (i.e. radd)
        # use `add` and swap the arguments
        if not op_func and name.startswith('r'):
            op_func = getattr(operator, name[1:], None)
            if op_func:
                @wraps(op_func)
                def op_func_swapped(left, right, *args, **kwargs):
                    """Right version of op_func"""
                    return op_func(right, left, *args, **kwargs)

                return op_func_swapped

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
