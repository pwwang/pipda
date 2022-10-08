"""Provide definition for functions that used as verb arguments"""
from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Mapping, TYPE_CHECKING
from functools import update_wrapper

from .utils import evaluate_expr, has_expr, update_user_wrapper
from .expression import Expression

if TYPE_CHECKING:
    from inspect import BoundArguments
    from .context import ContextType
    from .verb import Verb


class FunctionCall(Expression):
    """A function call object that awaits for evaluation

    Args:
        func: A registered function by `register_func` or an expression,
            for example, `f.col.mean`
        args: and
        kwargs: The arguments for the function
    """

    def __init__(
        self,
        func: Function | Verb | Expression,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._pipda_func = func
        self._pipda_args = args
        self._pipda_kwargs = kwargs

    def __str__(self) -> str:
        """Representation of the function call"""
        strargs: List[str] = []
        funname = str(self._pipda_func)
        if self._pipda_args:
            strargs.extend((str(arg) for arg in self._pipda_args))
        if self._pipda_kwargs:
            strargs.extend(
                f"{key}={val}" for key, val in self._pipda_kwargs.items()
            )
        return f"{funname}({', '.join(strargs)})"

    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        """Evaluate the function call"""
        func = self._pipda_func
        if isinstance(func, Expression):
            # f.a(1)
            func = evaluate_expr(func, data, context)
            # Evaluate the expression using the context passed by
            return func(
                *(
                    evaluate_expr(arg, data, context)
                    for arg in self._pipda_args
                ),
                **{
                    key: evaluate_expr(val, data, context)
                    for key, val in self._pipda_kwargs.items()
                },
            )

        context = func.contexts["_"] or context
        extra_contexts = func.extra_contexts["_"]

        if extra_contexts:
            bound = func.bind_arguments(*self._pipda_args, **self._pipda_kwargs)

            for key, val in bound.arguments.items():
                ctx = extra_contexts.get(key, context)
                val = evaluate_expr(val, data, ctx)
                bound.arguments[key] = val

            return func.func(*bound.args, **bound.kwargs)

        # we don't need signature if there is no extra context
        return func.func(
            *(evaluate_expr(arg, data, context) for arg in self._pipda_args),
            **{
                key: evaluate_expr(val, data, context)
                for key, val in self._pipda_kwargs.items()
            },
        )


class Registered(ABC):
    """Base function for registered function/verb"""

    def __str__(self):
        """Used to stringify the whole expression"""
        return self.func.__name__

    @property
    def signature(self):
        # cached property returns None for numpy.vectorize() object
        if not self._signature:
            self._signature = inspect.signature(self.func)
        return self._signature

    def bind_arguments(self, *args, **kwargs: Any) -> BoundArguments:
        boundargs = self.signature.bind(*args, **kwargs)
        boundargs.apply_defaults()
        return boundargs

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call a registered function/verb"""


class Function(Registered):
    """Registered function

    Args:
        func: The original function
        context: The context
        extra_context: The extra context for keyword arguments
    """

    def __init__(
        self,
        func: Callable,
        context: ContextType,
        extra_contexts: Mapping[str, ContextType],
        name: str = None,
        qualname: str = None,
        doc: str = None,
        module: str = None,
        signature: inspect.Signature = None,
    ) -> None:
        self.func = func
        self.contexts = {"_": context}
        self.extra_contexts = {"_": extra_contexts}
        self._signature = signature

        update_wrapper(self, self.func)
        update_user_wrapper(
            self,
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call a registered function"""
        # No arguments, call the function directly
        if not args and not kwargs:
            return self.func()

        if has_expr(args) or has_expr(kwargs):
            return FunctionCall(self, *args, **kwargs)

        # No expression arguments, call the function directly
        return self.func(*args, **kwargs)


def register_func(
    func: Callable = None,
    *,
    context: ContextType = None,
    extra_contexts: Mapping[str, ContextType] = None,
    name: str = None,
    qualname: str = None,
    doc: str = None,
    module: str = None,
    signature: inspect.Signature = None,
) -> Function | Callable:
    """Register a function to be used as a verb argument so that they don't
    get evaluated immediately

    Args:
        func: The original function
        context: The context used to evaluate the arguments
        extra_contexts: Extra contexts to evaluate keyword arguments
        name: and
        qualname: and
        doc: and
        module: and
        signature: The meta information about the function to overwrite `func`'s
            or when it's not available from `func`

    Returns:
        A registered `Function` object, or a decorator if `func` is not given
    """
    if func is None:
        return lambda fun: register_func(
            fun,
            context=context,
            extra_contexts=extra_contexts or {},
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
            signature=signature,
        )

    return Function(
        func,
        context,
        extra_contexts or {},
        name=name,
        qualname=qualname,
        doc=doc,
        module=module,
        signature=signature,
    )
