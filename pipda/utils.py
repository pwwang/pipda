"""Provide utilities"""
from __future__ import annotations

import ast
import sys
from enum import Enum
from functools import singledispatch
from typing import Any
import warnings

from .context import ContextType


class VerbCallingCheckWarning(Warning):
    """Warns when checking verb is called normally or using piping"""


class VerbCallingCheckError(Exception):
    """Raises when checking verb is called normally or using piping"""


def is_piping_verbcall(verb: str, fallback: str) -> bool:
    """Check if the verb is called with piping.

    Example:
        >>> data >> verb(...)
        >>> data >>= verb(...)

    Args:
        verb: The name of the verb, used in warning or exception messaging
        fallback: What if the AST node fails to retrieve?
            piping - Suppose this verb is called like `data >> verb(...)`
            normal - Suppose this verb is called like `verb(data, ...)`
            piping_warning - Suppose piping call, but show a warning
            normal_warning - Suppose normal call, but show a warning
            raise - Raise an error

    Returns:
        True if it is a piping verb call, otherwise False
    """
    from executing import Source
    from .verb import PIPING_OPS, VerbCall

    frame = sys._getframe(2)
    node = Source.executing(frame).node

    if not node:
        # Using fallbacks
        if fallback == "normal":
            return False
        if fallback == "piping":
            return True
        if fallback == "normal_warning":
            warnings.warn(
                f"Failed to detect AST node calling `{verb}`, "
                "assuming a normal call.",
                VerbCallingCheckWarning
            )
            return False
        if fallback == "piping_warning":
            warnings.warn(
                f"Failed to detect AST node calling `{verb}`, "
                "assuming a piping call.",
                VerbCallingCheckWarning
            )
            return True

        raise VerbCallingCheckError(
            f"Failed to detect AST node calling `{verb}` "
            "without a fallback solution."
        )

    try:
        parent = node.parent
    except AttributeError:  # pragma: no cover
        return False

    return (
        (
            (isinstance(parent, ast.BinOp) and parent.right is node)
            or (isinstance(parent, ast.AugAssign) and parent.value is node)
        )
        and isinstance(parent.op, PIPING_OPS[VerbCall.PIPING][1])
    )


def evaluate_expr(expr: Any, data: Any, context: ContextType) -> Any:
    """Evaluate a mixed expression"""
    if isinstance(context, Enum):
        context = context.value

    if hasattr(expr.__class__, "_pipda_eval"):
        # Not only for Expression objects, but also
        # allow customized classes
        return expr._pipda_eval(data, context)

    if isinstance(expr, (tuple, list, set)):
        # In case it's subclass
        return expr.__class__(
            (evaluate_expr(elem, data, context) for elem in expr)
        )

    if isinstance(expr, slice):
        return slice(
            evaluate_expr(expr.start, data, context),
            evaluate_expr(expr.stop, data, context),
            evaluate_expr(expr.step, data, context),
        )

    if isinstance(expr, dict):
        return expr.__class__(
            {
                key: evaluate_expr(val, data, context)
                for key, val in expr.items()
            }
        )
    return expr


@singledispatch
def has_expr(expr: Any) -> bool:
    """Check if expr has any Expression object in it"""
    from .expression import Expression

    return isinstance(expr, Expression)


@has_expr.register(tuple)
@has_expr.register(list)
@has_expr.register(set)
def _(expr: Any) -> Any:
    return any(has_expr(elem) for elem in expr)


@has_expr.register(slice)
def _(expr: Any) -> Any:
    return has_expr((expr.start, expr.stop, expr.step))


@has_expr.register(dict)
def _(expr: Any) -> Any:
    return any(has_expr(elem) for elem in expr.values())
