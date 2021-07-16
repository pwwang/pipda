"""Provides register_func to register functions"""
from typing import Any, Callable, Mapping, Tuple, Type, Union
from .utils import (
    NULL,
    InaccessibleToNULLException,
    bind_arguments,
    evaluate_expr,
)
from .expression import Expression
from .context import ContextBase, ContextError


class Function(Expression):
    """The Function class, defining how the function should be executed
    when needed

    Args:
        func: The function to execute
        context: The context to evaluate the Reference/Operator objects

    Attributes:
        func: The function
        context: The context
        args: The arguments of the function
        kwargs: The keyword arguments of the function
        dataarg: Whether the function has data as the first argument
    """

    def __init__(
        self,
        func: Union[Callable, Expression],
        args: Tuple,
        kwargs: Mapping[str, Any],
        dataarg: bool = True,
    ) -> None:

        self._pipda_func = func
        self._pipda_args = args
        self._pipda_kwargs = kwargs
        self._pipda_dataarg = dataarg

    def __repr__(self) -> str:
        if isinstance(self._pipda_func, Expression):
            func = repr(self._pipda_func)
        else:
            func = self._pipda_func.__qualname__

        return (
            f"{self.__class__.__name__}"
            f"(func={func}, dataarg={self._pipda_dataarg})"
        )

    def _pipda_eval(
        self, data: Any, context: ContextBase = None
    ) -> Any:
        """Execute the function with the data

        The context will be determined by the function itself, so
        the context argument will not be used, since it will not override
        the context of the function
        """
        # don't change at 2nd evaluation
        # in case we have f.col.mean()
        func = self._pipda_func
        if isinstance(func, Expression):
            func = evaluate_expr(func, data, context)

        dispatcher = _get_dispatcher(func, type(data))  # type: ignore
        func_context = getattr(dispatcher, "context", None)
        func_extra_contexts = getattr(dispatcher, "extra_contexts", None)

        context = func_context or context
        args = (
            (data, *self._pipda_args)
            if self._pipda_dataarg
            else self._pipda_args
        )
        bondargs = bind_arguments(dispatcher, args, self._pipda_kwargs)
        if func_extra_contexts:
            # evaluate some specfic args
            for key, ctx in func_extra_contexts.items():
                if key not in bondargs.arguments:
                    raise KeyError(
                        f"[{dispatcher.__qualname__}] No such argument: {key!r}"
                    )
                bondargs.arguments[key] = evaluate_expr(
                    bondargs.arguments[key], data, ctx
                )

        if "_context" in bondargs.arguments:
            bondargs.arguments["_context"] = context

        if context and context.name == "pending":
            # leave args/kwargs for the child
            # verb/function/operator to evaluate
            return func(*bondargs.args, **bondargs.kwargs)  # type: ignore

        args = evaluate_expr(
            bondargs.args, data, context.args if context else context
        )
        kwargs = evaluate_expr(
            bondargs.kwargs, data, context.kwargs if context else context
        )
        return func(*args, **kwargs)  # type: ignore


class FastEvalFunction(Function):
    """Fast evaluation function"""

    def _pipda_fast_eval(self):
        """Evaluate this function"""
        try:
            return self._pipda_eval(NULL)
        except (ContextError, InaccessibleToNULLException, NotImplementedError):
            return self


# Helper functions --------------------------------


def _get_dispatcher(func: Callable, typ: Type) -> Callable:
    dispatch = getattr(func, "dispatch", None)
    if dispatch is None:
        return func

    return dispatch(typ)
