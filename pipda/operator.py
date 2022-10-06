"""Provide operators"""
from __future__ import annotations

import operator
from typing import Any, Callable, Type, TYPE_CHECKING

from .utils import evaluate_expr
from .expression import Expression, OPERATORS

if TYPE_CHECKING:
    from .context import ContextType


class OperatorCall(Expression):
    """The operator call

    Args:
        op_func: The function to handle the call
        op_name: The name of the operator
        operands: The operands of the operator
    """

    def __init__(self, op_func: Callable, op_name: str, *operands: Any) -> None:
        self._pipda_op_func = op_func
        self._pipda_op_name = op_name
        self._pipda_operands = operands

    def __str__(self):
        """String representation of the operator call"""
        op, right = OPERATORS[self._pipda_op_name]
        if right:
            return f" {op} ".join(
                reversed([str(operand) for operand in self._pipda_operands])
            )
        if len(self._pipda_operands) == 1:
            return f"{op}{str(self._pipda_operands[0])}"

        return f" {op} ".join(str(operand) for operand in self._pipda_operands)

    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        """Evaluate the operator call"""
        operands = (
            evaluate_expr(arg, data, context)
            for arg in self._pipda_operands
        )
        return self._pipda_op_func(*operands)


class Operator:
    """Defines the operators

    By default, it inherits the operator from the builtin `operator` library

    You can define you own operators by subclass this class and decorated it
    using `register_operator`.

    Examples:
        >>> @register_operator
        >>> class MyOperator(Operator):
        >>>     def add(self, x, y):
        >>>         return x * y
    """
    def __getattr__(self, name: str) -> Callable:
        if not OPERATORS[name][1]:
            # not a right operator (e.g. radd)
            return getattr(operator, name)

        name = name[1:]
        return lambda x, y: getattr(operator, name)(y, x)


def register_operator(opclass: Type) -> Type:
    """Register a operator class

    Can be worked as a decorator
    >>> @register_operator
    >>> class MyOperator(Operator):
    >>>     ...

    Args:
        opclass: A subclass

    Returns:
        The opclass
    """
    from .expression import Expression
    Expression._pipda_operator = opclass()
    return opclass
