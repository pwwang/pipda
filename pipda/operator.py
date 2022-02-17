"""Provide the Operator class"""
from contextlib import suppress
import operator
from enum import Enum
from collections import namedtuple
from functools import wraps
from typing import Any, Callable, Mapping, Tuple, ClassVar, Type

from .context import ContextAnnoType, ContextBase
from .function import Function


OperatorAttrs = namedtuple("OperatorAttrs", ["sign", "unary", "right"])


OPERATOR_MAPS = {
    "add": OperatorAttrs("+", False, False),
    "radd": OperatorAttrs("+", False, True),
    "sub": OperatorAttrs("-", False, False),
    "rsub": OperatorAttrs("-", False, True),
    "mul": OperatorAttrs("*", False, False),
    "rmul": OperatorAttrs("*", False, True),
    "matmul": OperatorAttrs("@", False, False),
    "rmatmul": OperatorAttrs("@", False, True),
    "truediv": OperatorAttrs("/", False, False),
    "rtruediv": OperatorAttrs("/", False, True),
    "floordiv": OperatorAttrs("//", False, False),
    "rfloordiv": OperatorAttrs("//", False, True),
    "mod": OperatorAttrs("%", False, False),
    "rmod": OperatorAttrs("%", False, True),
    "lshift": OperatorAttrs("<<", False, False),
    "rlshift": OperatorAttrs("<<", False, True),
    "rshift": OperatorAttrs(">>", False, False),
    "rrshift": OperatorAttrs(">>", False, True),
    "and_": OperatorAttrs("&", False, False),
    "rand_": OperatorAttrs("&", False, True),
    "xor": OperatorAttrs("^", False, False),
    "rxor": OperatorAttrs("^", False, True),
    "or_": OperatorAttrs("|", False, False),
    "ror_": OperatorAttrs("|", False, True),
    "pow": OperatorAttrs("**", False, False),
    "rpow": OperatorAttrs("**", False, True),
    "lt": OperatorAttrs("<", False, False),
    "le": OperatorAttrs("<=", False, False),
    "eq": OperatorAttrs("==", False, False),
    "ne": OperatorAttrs("!=", False, False),
    "gt": OperatorAttrs(">", False, False),
    "ge": OperatorAttrs(">=", False, False),
    "neg": OperatorAttrs("-", True, False),
    "pos": OperatorAttrs("+", True, False),
    "invert": OperatorAttrs("~", True, False),
}


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

    def __str__(self) -> str:
        sign = OPERATOR_MAPS[self.op].sign
        if OPERATOR_MAPS[self.op].unary:
            return f"{sign}{self._pipda_args[0]}"
        if not OPERATOR_MAPS[self.op].right:
            return f"{self._pipda_args[0]} {sign} {self._pipda_args[1]}"
        return f"{self._pipda_args[1]} {sign} {self._pipda_args[0]}"

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

    def _find_op_func(self, opname: str) -> Callable:
        """Find the function correspoind to the opname

        Note that there is no prefix to the opname and no right version of it
        """
        self_op_name = f"_op_{opname}"
        # if it is defined with the class
        if self_op_name in dir(self):
            return getattr(self, self_op_name)

        # otherwise use standard operator function
        return getattr(operator, opname, None)

    def _get_op_func(self) -> Callable:
        """Get the operator function from the operator module by name"""
        if self.op not in OPERATOR_MAPS:
            raise ValueError(f"Not a valid operator: {self.op!r}")

        if not OPERATOR_MAPS[self.op].right:
            op_func = self._find_op_func(self.op)
            with suppress(AttributeError):
                op_func.__qualname__ = self.op

            return op_func

        # if self.op[0] == 'r':
        # if we get radd, swap left and right operands
        op_func = self._find_op_func(self.op[1:])

        @wraps(op_func)
        def left_op_func(arg_a, arg_b, *args, **kwargs):
            return op_func(arg_b, arg_a, *args, **kwargs)

        left_op_func.__qualname__ = self.op
        return left_op_func
