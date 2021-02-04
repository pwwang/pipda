"""Provides register_common to register common functions that don't need
the piped-in data to execute.
"""

from functools import wraps
from types import FunctionType
from typing import Any, Callable, Optional
from .utils import (
    Context,
    Predicate,
    evaluate_args,
    evaluate_kwargs,
    is_piping
)

class CommonFunction(Predicate):
    """The common function class"""
    def __init__(self, func: Callable, context: Context = Context.DATA):
        super().__init__(func, context)
        self.func = func
        self.args = self.kwargs = None

    def evaluate(self, data: Any, context: Context = Context.UNSET) -> Any:
        """Execute the function with the data and context

        Just ignore the data.
        """
        args = evaluate_args(self.args, data, self.context)
        kwargs = evaluate_kwargs(self.kwargs, data, self.context)
        return self.func(*args, **kwargs)

def register_common(
        func: Optional[FunctionType] = None,
        context: Context = Context.DATA
) -> Callable:
    """Register common functions that don't need piped-in data"""
    if context == Context.UNSET:
        raise ValueError(
            f"Common functions cannot be registered with {Context.UNSET}"
        )

    if func is None:
        return lambda fun: register_common(fun, context)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        force_piping = kwargs.pop('_force_piping', False)
        if force_piping or is_piping():
            predicate = CommonFunction(func, context)
            return predicate.defer(args, kwargs)
        return func(*args, **kwargs)

    wrapper.__pipda__ = CommonFunction.__name__

    return wrapper
