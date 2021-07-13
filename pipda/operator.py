"""Provide the Operator class"""
import operator
from enum import Enum
from functools import wraps
from typing import Any, Callable, Mapping, Tuple, ClassVar, Type

from .context import ContextAnnoType, ContextBase
from .function import Function


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

    REGISTERED: ClassVar[Type["Operator"]] = None

    def __init__(
        self,
        op: str,
        args: Tuple,
        kwargs: Mapping[str, Any],
        datarg: bool = False,
    ) -> None:

        self.op = op
        self.data = None
        op_func = self._get_op_func()
        super().__init__(op_func, args, kwargs, datarg)

    @staticmethod
    def set_context(
        context: ContextAnnoType,
        extra_contexts: Mapping[str, ContextAnnoType] = None,
    ) -> Callable[[Callable], Callable]:
        """Set custom context for a operator method"""

        def wrapper(func):
            func.context = (
                context.value if isinstance(context, Enum) else context
            )
            extra_contexts2 = extra_contexts or {}
            func.extra_contexts = {
                key: ctx.value if isinstance(ctx, Enum) else ctx
                for key, ctx in extra_contexts2.items()
            }
            return func

        return wrapper

    def _pipda_eval(
        self, data: Any, context: ContextBase = None
    ) -> Any:
        """Evaluate the operator

        No data passed to the operator function. It should be used to evaluate
        the arguments.
        """
        # set the context and data in case they need to be used
        # inside the function.
        self.data = data
        return super()._pipda_eval(data, context)

    def _get_op_func(self) -> Callable:
        """Get the operator function from the operator module by name"""
        def _opfunc(opname: str) -> Callable:
            self_op_name = f"_op_{opname}"
            if hasattr(self.__class__, self_op_name):
                return getattr(self, self_op_name)

            return getattr(operator, opname, None)

        op_func = _opfunc(self.op)
        if op_func:
            return op_func

        if self.op[0] == 'r':
            # if we get radd, swap left and right operands
            op_func = _opfunc(self.op[1:])
            if op_func:
                @wraps(op_func)
                def left_op_func(arg_a, arg_b, *args, **kwargs):
                    return op_func(arg_b, arg_a, *args, **kwargs)

                return left_op_func

        raise ValueError(
            f"No operator function defined for {self.op!r}"
        )
