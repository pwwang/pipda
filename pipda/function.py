"""Provides register_func to register functions"""
from typing import (
    Any, Callable, Mapping, Optional, Tuple, Type, Union
)
from .utils import (
    Expression,
    bind_arguments,
    evaluate_args,
    evaluate_expr,
    evaluate_kwargs
)
from .context import ContextBase

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
            args: Tuple[Any],
            kwargs: Mapping[str, Any],
            dataarg: bool = True
    ) -> None:

        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.dataarg = dataarg

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}'
            f'(func={self.func.__qualname__!r}, dataarg={self.dataarg})'
        )

    def _pipda_eval(
            self,
            data: Any,
            context: Optional[ContextBase] = None
    ) -> Any:
        """Execute the function with the data

        The context will be determined by the function itself, so
        the context argument will not be used, since it will not override
        the context of the function
        """
        # don't change at 2nd evaluation
        # in case we have f.col.mean()
        func = self.func
        if isinstance(func, Expression):
            func = evaluate_expr(func, data, context)

        dispatcher = _get_dispatcher(func, type(data))
        func_context = getattr(dispatcher, 'context', None)
        func_extra_contexts = getattr(dispatcher, 'extra_contexts', None)

        context = func_context or context
        args = (data, *self.args) if self.dataarg else self.args
        bondargs = bind_arguments(dispatcher, args, self.kwargs)
        if func_extra_contexts:
            # evaluate some specfic args
            for key, ctx in func_extra_contexts.items():
                if key not in bondargs.arguments:
                    raise KeyError(f'No such argument: {key!r}')
                bondargs.arguments[key] = evaluate_expr(
                    bondargs.arguments[key], data, ctx
                )

        if '_context' in bondargs.arguments:
            bondargs.arguments['_context'] = context

        if context and context.name == 'pending':
            # leave args/kwargs for the child
            # verb/function/operator to evaluate
            return func(*bondargs.args, **bondargs.kwargs)

        args = evaluate_args(
            bondargs.args,
            data,
            context.args if context else context
        )
        kwargs = evaluate_kwargs(
            bondargs.kwargs,
            data,
            context.kwargs if context else context
        )
        return func(*args, **kwargs)

# Helper functions --------------------------------

def _get_dispatcher(func: Callable, typ: Type) -> Callable:
    dispatch = getattr(func, 'dispatch', None)
    if dispatch is None:
        return func

    return dispatch(typ)
