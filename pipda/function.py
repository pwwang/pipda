"""Provides register_func to register functions"""
from functools import singledispatch, wraps
from types import FunctionType
from typing import (
    Any, Callable, Iterable, Mapping, Optional, Tuple, Type, Union
)
from .utils import (
    Expression, NULL, evaluate_args, evaluate_kwargs, is_piping
)
from .context import Context, ContextBase, ContextEval, ContextMixed

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
        datarg: Whether the function has data as the first argument
    """

    def __init__(self,
                 func: Callable,
                 context: ContextBase,
                 args: Tuple[Any],
                 kwargs: Mapping[str, Any],
                 datarg: bool = True):
        super().__init__(context)

        if not datarg:
            self.func = wraps(func)(
                lambda _data, *args, **kwargs: func(*args, **kwargs)
            )
        else:
            self.func = func
        self.args = args
        self.kwargs = kwargs

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(func={self.func.__qualname__!r})'

    def evaluate(
            self,
            data: Any,
            context: Optional[ContextBase] = None
    ) -> Any:
        """Execute the function with the data

        The context will be determined by the function itself, so
        the context argument will not be used, since it will not override
        the context of the function
        """
        context = self.context or context

        if not context:
            # leave args/kwargs for the verb/function/operator to evaluate
            return self.func(data, *self.args, **self.kwargs)

        args = evaluate_args(self.args, data, context.args)
        kwargs = evaluate_kwargs(self.kwargs, data, context.kwargs)
        return self.func(data, *args, **kwargs)

def _register_function_no_datarg(
        context: Optional[ContextBase],
        func: Callable
) -> Callable:
    """Register functions without data as the first argument"""
    @wraps(func)
    def wrapper(*args: Any, _force_piping: bool = False, **kwargs: Any) -> Any:
        if _force_piping or is_piping():
            return Function(func, context, args, kwargs, False)

        return func(*args, **kwargs)

    wrapper.__pipda__ = 'PlainFunction'
    return wrapper

def _register_function_datarg(
        cls: Iterable[Type],
        context: Optional[ContextBase],
        func: Callable
) -> Callable:
    """Register functions with data as the first argument"""
    @singledispatch
    @wraps(func)
    def generic(_data: Any, *args: Any, **kwargs: Any) -> Any:
        if object in cls:
            return func(_data, *args, **kwargs)
        raise NotImplementedError(
            f'{func.__name__!r} not registered '
            f'for type: {type(_data)}.'
        )

    for one_cls in cls:
        if one_cls is not object:
            generic.register(one_cls, func)

    @wraps(func)
    def wrapper(*args: Any,
                _force_piping: bool = False,
                **kwargs: Any) -> Any:
        if _force_piping or is_piping():
            return Function(generic, context, args, kwargs)
        return func(*args, **kwargs)

    wrapper.register = generic.register
    wrapper.registry = generic.registry
    wrapper.dispatch = generic.dispatch
    wrapper.__pipda__ = 'Function'

    return wrapper

def register_func(
        cls: Union[FunctionType, Type, Iterable[Type]] = object,
        context: Optional[Union[Context, ContextBase]] = NULL,
        func: Optional[FunctionType] = None
) -> Callable:
    """Register a function to be used in verb

    when cls is None, meaning the function doesn't have data as the first
    argument
    """
    if func is None and isinstance(cls, FunctionType):
        func, cls = cls, object
    if func is None:
        return lambda fun: register_func(cls, context, fun)

    if isinstance(context, Context):
        context = context.value

    if cls is None:
        if context is NULL:
            context = ContextEval()
        return _register_function_no_datarg(context, func)

    if not isinstance(cls, (tuple, list, set)):
        cls = (cls, )

    if context is NULL:
        context = ContextMixed()
    return _register_function_datarg(cls, context, func)
