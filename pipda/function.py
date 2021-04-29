"""Provides register_func to register functions"""
from enum import Enum
import inspect
from functools import singledispatch, wraps
from types import FunctionType
from typing import (
    Any, Callable, Iterable, Mapping, Optional, Tuple, Type, Union
)
from .utils import (
    Expression,
    evaluate_args, evaluate_expr, evaluate_kwargs, calling_env, have_expr,
    singledispatch_register, logger
)
from .context import (
    ContextAnnoType, ContextBase
)

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
                 args: Tuple[Any],
                 kwargs: Mapping[str, Any],
                 datarg: bool = True):

        self.func = func
        self.datarg = datarg
        self.args = args
        self.kwargs = kwargs

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(func={self.func.__qualname__!r})'

    def __call__(
            self,
            data: Any,
            context: Optional[ContextBase] = None,
            level: int = 0
    ) -> Any:
        """Execute the function with the data

        The context will be determined by the function itself, so
        the context argument will not be used, since it will not override
        the context of the function
        """
        dispatch = getattr(self.func, 'dispatch', None)
        func_context = None
        func_extra_contexts = None
        dispatcher = self.func
        if dispatch is not None:
            dispatcher = dispatch(type(data))
        func_context = getattr(dispatcher, 'context', None)
        func_extra_contexts = getattr(dispatcher, 'extra_contexts', None)

        context = func_context or context

        # The main context has to be set
        # if not context: # still unset
        #     raise ContextError(
        #         f'Cannot evaluate {self!r} with an unset context.'
        #     )

        args = (data, *self.args) if self.datarg else self.args
        kwargs = self.kwargs.copy()
        signature = inspect.signature(dispatcher)
        if '_context' in signature.parameters:
            kwargs['_context'] = None

        bondargs = signature.bind(*args, **kwargs)
        bondargs.apply_defaults()

        if self.__class__.__name__ == 'Verb':
            level = 0

        prefix = '- ' if level == 0 else '  ' * level
        logger.debug('%sEvaluating %r with context %r.', prefix, self, context)
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
            return self.func(*bondargs.args, **bondargs.kwargs)

        args = evaluate_args(
            bondargs.args,
            data,
            context.args if context else context,
            level
        )
        kwargs = evaluate_kwargs(
            bondargs.kwargs,
            data,
            context.kwargs if context else context,
            level
        )
        return self.func(*args, **kwargs)

def _register_function_no_datarg(
        func: Callable,
        verb_arg_only: bool,
) -> Callable:
    """Register functions without data as the first argument"""

    @wraps(func)
    def wrapper(
            *args: Any,
            _env: Optional[str] = None,
            **kwargs: Any
    ) -> Any:
        _env = (
            calling_env(register_func.astnode_fail_warning)
            if _env is None else _env
        )

        # As argument of a verb
        if isinstance(_env, str) and _env == 'piping':
            return Function(func, args, kwargs, False)

        if verb_arg_only and _env is None:
            raise ValueError(
                f"`{func.__qualname__}` must only be used inside verbs"
            )

        # Otherwise I am standalone
        if have_expr(args, kwargs) and _env is None:
            return Function(func, args, kwargs, False)

        if _env is None:
            return func(*args, **kwargs)
        return Function(func, args, kwargs, False)(_env)

    wrapper.__pipda__ = 'PlainFunction'
    wrapper.__origfunc__ = func
    return wrapper

def _register_function_datarg(
        cls: Iterable[Type],
        func: Callable,
        verb_arg_only: bool
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
    def wrapper(
            *args: Any,
            _env: Optional[str] = None,
            **kwargs: Any
    ) -> Any:
        _env = (
            calling_env(register_func.astnode_fail_warning)
            if _env is None else _env
        )

        # As argument of a verb
        if isinstance(_env, str) and _env == 'piping':
            return Function(generic, args, kwargs)

        if verb_arg_only and _env is None:
            raise ValueError(
                f"`{func.__qualname__}` must only be used inside verbs"
            )

        # If nothing passed, assuming waiting for the data coming in to evaluate
        # Not expanding this to complicated situations
        if not args and not kwargs and _env is None:
            return Function(generic, args, kwargs)

        if have_expr(args[1:], kwargs):
            return Function(generic, args[1:], kwargs)(args[0])

        if _env is None:
            return generic(*args, **kwargs)

        # context data
        return Function(generic, args, kwargs)(_env)

    wrapper.register = singledispatch_register(generic.register)
    wrapper.registry = generic.registry
    wrapper.dispatch = generic.dispatch
    wrapper.__pipda__ = 'Function'
    wrapper.__origfunc__ = func

    return wrapper

def register_func(
        cls: Union[FunctionType, Type, Iterable[Type]] = object,
        context: Optional[ContextAnnoType] = None,
        func: Optional[FunctionType] = None,
        verb_arg_only: bool = False,
        extra_contexts: Optional[Mapping[str, ContextAnnoType]] = None,
        **attrs: Any
) -> Callable:
    """Register a function to be used in verb

    when cls is None, meaning the function doesn't have data as the first
    argument
    """
    if func is None and isinstance(cls, FunctionType):
        func, cls = cls, object
    if func is None:
        return lambda fun: register_func(
            cls,
            context,
            fun,
            verb_arg_only,
            extra_contexts,
            **attrs
        )

    if isinstance(context, Enum):
        context = context.value

    for name, attr in attrs.items():
        setattr(func, name, attr)
    func.context = context

    extra_contexts = extra_contexts or {}
    func.extra_contexts = {
        key: ctx.value if isinstance(ctx, Enum) else ctx
        for key, ctx in extra_contexts.items()
    }

    if cls is None:
        return _register_function_no_datarg(
            func,
            verb_arg_only
        )

    if not isinstance(cls, (tuple, list, set)):
        cls = (cls, )

    return _register_function_datarg(
        cls,
        func,
        verb_arg_only
    )

register_func.astnode_fail_warning = True
