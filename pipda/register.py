"""Provide register_* suite"""
import ast
import inspect
import warnings
from collections import namedtuple
from enum import Enum
from functools import singledispatch, wraps, lru_cache
from itertools import chain
from types import FunctionType
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union
)

from .context import ContextBase, ContextAnnoType
from .function import Function
from .utils import Expression, NULL, PipingEnvs, bind_arguments, calling_env
from .verb import Verb
from .operator import Operator

# The Sign tuple
Sign = namedtuple('Sign', ['method', 'token'])

# All supported signs
#   method is used to be attached to verbs
#   ast token class is used to check if the verb or function
#       is running in piping mode
PIPING_SIGNS = {
    '+': Sign('__radd__', ast.Add),
    '-': Sign('__rsub__', ast.Sub),
    '*': Sign('__rmul__', ast.Mult),
    '@': Sign('__rmatmul__', ast.MatMult),
    '/': Sign('__rtruediv__', ast.Div),
    '//': Sign('__rfloordiv__', ast.FloorDiv),
    '%': Sign('__rmod__', ast.Mod),
    '**': Sign('__rpow__', ast.Pow),
    '<<': Sign('__rlshift__', ast.LShift),
    '>>': Sign('__rrshift__', ast.RShift),
    '&': Sign('__rand__', ast.BitAnd),
    '^': Sign('__rxor__', ast.BitXor),
    '|': Sign('__ror__', ast.BitOr)
}

def register_piping(sign: str) -> None:
    """Register a piping sign for the verbs

    This actually attaches the `_pipda_eval` method to the method defined
    in `PIPING_SIGNS`.

    Args:
        sign: One of the signs in `PIPING_SIGNS`
    """
    if sign not in PIPING_SIGNS:
        raise ValueError(f"Unsupported piping sign: {sign}")

    if Verb.CURRENT_SIGN:
        current_sign = PIPING_SIGNS[Verb.CURRENT_SIGN]
        delattr(Verb, current_sign.method)

    Verb.CURRENT_SIGN = sign
    new_sign = PIPING_SIGNS[sign]
    setattr(Verb, new_sign.method, Verb._pipda_eval)

def register_verb(
        types: Union[FunctionType, Type, Iterable[Type]] = object,
        context: ContextAnnoType = None,
        func: Optional[FunctionType] = None,
        extra_contexts: Optional[Mapping[str, ContextAnnoType]] = None,
        **attrs: Any
) -> Callable:
    """Register a verb with specific types of data

    If `func` is not given (works like `register_verb(cls, context=...)`),
    it returns a function, works as a decorator.

    For example
        >>> @register_verb(DataFrame, context=Context.EVAL)
        >>> def verb(data, ...):
        >>>     ...

    When function is passed as a non-keyword argument, other arguments are as
    defaults
        >>> @register_verb
        >>> def verb(data, ...):
        >>>     ...

    In such a case, it is like a generic function to work with all types of
    data.

    Args:
        types: The types of data for the verb
            Multiple types are supported to be passed as a list/tuple/set.
            It cannot be None for verbs.
        context: The context to evaluate the Expression objects
        func: The function to be decorated if passed explicitly
        extra_contexts: Extra contexts (if not the same as `context`)
            for specific arguments
        **attrs: Other attributes to be attached to the function

    Returns:
        A decorator function if `func` is not given or a wrapper function
        like a singledispatch generic function that can register other types,
        show all registry and dispatch for a specific type
    """
    types, context, func, extra_contexts = _clean_register_args(
        types,
        context,
        func,
        extra_contexts
    )

    if func is None:
        return lambda fun: register_verb(
            types, context, fun, extra_contexts, **attrs
        )

    if types is None:
        raise ValueError(
            'Verbs must be registered with data argument '
            '(`types` cannot be None)'
        )

    for name, attr in attrs.items():
        setattr(func, name, attr)

    # allow register to have different context
    func.context = context
    func.extra_contexts = extra_contexts

    generic = _generializing(func, types)
    return _wrapping_dataarg(generic, 'Verb')


def register_func(
        types: Union[FunctionType, Type, Iterable[Type]] = object,
        context: Optional[ContextAnnoType] = None,
        func: Optional[FunctionType] = None,
        verb_arg_only: bool = False,
        extra_contexts: Optional[Mapping[str, ContextAnnoType]] = None,
        **attrs: Any
) -> Callable:
    """Register a function to be used in verb

    If `func` is not given (works like `register_verb(cls, context=...)`),
    it returns a function, works as a decorator.

    For example
        >>> @register_func(numpy.ndarray, context=Context.EVAL)
        >>> def func(data, ...):
        >>>     ...

    When function is passed as a non-keyword argument, other arguments are as
    defaults
        >>> @register_func
        >>> def func(data, ...):
        >>>     ...

    In such a case, it is like a generic function to work with all types of
    data.

    `data` is not a required argument. If not required, `cls` should be
    specified as `None`.

    Args:
        types: The classes of data for the verb
            Multiple classes are supported to be passed as a list/tuple/set.
            None means no data argument for the function
        context: The context to evaluate the Expression objects
        func: The function to be decorated if passed explicitly
        verb_arg_only: Whether the function should be only used as an argument
            of a verb. This means it only works in the format of
            >>> data >> verb(..., func(...), ...)
            Note that even this won't work
            >>> verb(data, ..., func(...), ...)
        extra_contexts: Extra contexts (if not the same as `context`)
            for specific arguments
        **attrs: Other attributes to be attached to the function

    Returns:
        A decorator function if `func` is not given or a wrapper function
        like a singledispatch generic function that can register other types,
        show all registry and dispatch for a specific type
    """
    types, context, func, extra_contexts = _clean_register_args(
        types,
        context,
        func,
        extra_contexts
    )

    if func is None:
        return lambda fun: register_func(
            types,
            context,
            fun,
            verb_arg_only,
            extra_contexts,
            **attrs
        )

    for name, attr in attrs.items():
        setattr(func, name, attr)

    # allow register to have different context
    func.context = context
    func.extra_contexts = extra_contexts

    if types is None:
        return _register_func_no_dataarg(func, verb_arg_only)

    return _register_func_dataarg(types, func, verb_arg_only)

def register_operator(op_class: Type[Operator]) -> Type[Operator]:
    """Register an Operator class

    Working as a decorator for a class subclassed from Operator.

    Args:
        op_class: The operator class

    Returns:
        The decorated operator class
    """
    if not issubclass(op_class, Operator):
        raise ValueError(
            "The operator class to be registered must be "
            "a subclass of pipda.Operator."
        )
    Operator.REGISTERED = op_class
    return op_class

def unregister(func: Callable) -> Callable:
    """Get the original function before register

    Args:
        func: The function that is either registered by
            `register_verb` or `register_func`

    Returns:
        The original function that before register
    """
    origfunc = getattr(func, '__origfunc__', None)
    if origfunc is None:
        raise ValueError(f'Function is not registered with pipda: {func}')
    return origfunc

# Helper functions --------------------------------

def _clean_register_args(
        types: Optional[Union[FunctionType, Type, Iterable[Type]]],
        context: ContextAnnoType,
        func: Optional[Callable],
        extra_contexts: Optional[Mapping[str, ContextAnnoType]]
) -> Tuple[
        Optional[Union[Type, Iterable[Type]]],
        Optional[ContextBase],
        Optional[Callable],
        Optional[Mapping[str, ContextBase]]
]:
    """Clean up the register_* arguments and get the right order"""
    if func is None and isinstance(types, FunctionType):
        func, types = types, object

    if types is not None and not isinstance(types, (tuple, set, list)):
        types = (types, )

    if isinstance(context, Enum):
        context = context.value

    extra_contexts = extra_contexts or {}
    extra_contexts = {
        key: ctx.value if isinstance(ctx, Enum) else ctx
        for key, ctx in extra_contexts.items()
    }

    return types, context, func, extra_contexts

def _generializing(func: Callable, types: Iterable[Type]) -> Callable:
    """Returns the generic function and register the types
    """
    if object in types:
        generic = singledispatch(func)
    else:
        # have to define this function here, so that every time a new function
        # is generated.
        # Otherwise, singledispatch mixed the registry when registering the
        # same function
        def _not_implemented(_data: Any, *args: Any, **kwargs: Any) -> None:
            raise NotImplementedError(
                f'{_not_implemented.__qualname__!r} is not '
                f'registered for type: {type(_data)}.'
            )
        # __name__ is used to tell if object is allowed
        _not_implemented.__qualname__ = func.__qualname__
        generic = singledispatch(_not_implemented)

    for typ in types:
        if typ is not object:
            generic.register(typ, func)

    generic.__origfunc__ = func
    return generic

def _wrapping_dataarg(
        generic: Callable,
        expr_class: str,
        verb_arg_only: Optional[bool] = None
) -> Callable:
    """Wrapping the generic function with data argument
    This basically defines how to run the function
    """
    @wraps(generic.__origfunc__)
    def wrapper(
            *args: Any,
            _env: Any = NULL,
            **kwargs: Any
    ) -> Any:
        _env = (
            calling_env(
                register_verb.astnode_fail_warning
                if expr_class == 'Verb'
                else register_func.astnode_fail_warning
            )
            if _env is NULL
            else _env
        )

        if _env is PipingEnvs.PIPING_VERB:
            # df >> verb(...)
            #       ^^^^^^^^^
            return Verb(generic, args, kwargs)

        # I am an argument of a verb
        # df >> verb(verb2(...))
        #            ^^^^^^^^^^
        if _env is PipingEnvs.PIPING:
            return Function(generic, args, kwargs, expr_class != 'Verb')

        if verb_arg_only is True and _env is NULL:
            raise ValueError(
                f"`{generic.__qualname__}` must only be used inside verbs."
            )

        return _try_calling_dataarg(
            generic,
            args,
            kwargs,
            _env
        )

    wrapper.register = _singledispatch_register(generic.register)
    wrapper.registry = generic.registry
    wrapper.dispatch = generic.dispatch
    wrapper.__pipda__ = expr_class
    wrapper.__origfunc__ = generic.__origfunc__

    return wrapper

def _wrapping_no_dataarg(
        generic: Callable,
        expr_class: str,
        verb_arg_only: Optional[bool] = None
) -> Callable:
    """Wrapping the generic function without data argument"""
    @wraps(generic)
    def wrapper(
            *args: Any,
            _env: Any = NULL,
            **kwargs: Any
    ) -> Any:
        _env = (
            calling_env(register_func.astnode_fail_warning)
            if _env is NULL else _env
        )

        # As argument of a verb
        if _env is PipingEnvs.PIPING:
            return Function(generic, args, kwargs, False)

        if verb_arg_only and _env is NULL:
            raise ValueError(
                f"`{generic.__qualname__}` must only be used inside verbs"
            )

        return _try_calling_no_dataarg(
            generic,
            args,
            kwargs,
            _env
        )

    wrapper.__pipda__ = expr_class
    wrapper.__origfunc__ = generic
    return wrapper

def _singledispatch_register(
        register: Callable[[Type, Callable], Callable]
) -> Callable[
        [Union[Type, Iterable[Type]], Any, Optional[Callable]],
        Callable
]:
    """Allow register of generic function to register types with context"""
    def _register_func(
            types: Union[Type, Iterable[Type]],
            context: Any = None,
            func: Optional[Callable] = None
    ) -> Callable:
        types, context, func, _ = _clean_register_args(
            types,
            context,
            func,
            None
        )

        if func is None:
            return lambda fun: _register_func(types, context, fun)

        func.context = context
        out = func
        for typ in types:
            out = register(typ, out)
        return out

    return _register_func

def _try_calling_dataarg(
        func: Callable,
        args: Tuple,
        kwargs: Mapping[str, Any],
        env: Any
) -> Any:
    """Try to call the function in a different ways.

    When should it be called regularly:
    1. Arguments can be successfully bound
    2. (None, *args) and kwargs cannot be bound
    That means it is for sure the regular calling. If not, 2) should be able
    to bind.

    So when you define/register functions, pay attention to the arguments
    with default values.

    Use as less arguments with default values as possible

    Otherwise, if env is not provided, an Function object is returned,
    pending for evaluation. If env (data) is provided, return the
    evaluated results, using the env
    """
    first_bind_error = None
    try:
        boundargs1 = bind_arguments(func.__origfunc__, args, kwargs)
    except TypeError as terr:
        first_bind_error = terr
        boundargs1 = None

    try:
        boundargs2 = bind_arguments(func.__origfunc__, (None, *args), kwargs)
    except TypeError:
        boundargs2 = None

    firstarg, rest_args, rest_kwargs = _strip_first_arg(args, kwargs)
    if boundargs1 and boundargs2:
        # with or without the data, arguments can be bound
        # like:
        # >>> def add(a, b, c=1): return a+b
        # >>> add(2, 3)
        # we have to determine whether the first argument can be dispatchable
        # If so it is a regular call: same as add(2, 3, 1)
        # otherwise, it is a piping call, waiting for evaluation
        #
        # firstarg is always not NULL since boundargs1 succeeded
        # this requires verbs/functions with data arg to be defined with first
        # argument non-optional.
        if _dispatchable(func, type(firstarg)):
            if _match_secondarg(func.__origfunc__):
                # The first argument can be dispatched and
                # can also be fit to the second argument
                # This causes the ambiguity
                warnings.warn(
                    f"Trying to calling `{func.__qualname__}` regularly. "
                    "However, ambiguity may occur to determine whether it "
                    "should be called regularly or return a Function object. "
                    "Take one/multiple of the following to avoid this: \n\n"
                    " 1. Use less optional arguments while "
                    "defining the function;\n"
                    " 2. Make sure second argument having a different type"
                    "annotation than the first; \n"
                    " 3. Specify values to the optional arguments "
                    "while calling.\n\n"
                    "Use the piping syntax if it is not the way you want.\n"
                )

            if _have_expr(rest_args, rest_kwargs):
                return (
                    Function(func, rest_args, rest_kwargs)._pipda_eval(
                        firstarg
                    )
                    if env is NULL
                    else Function(func, args, kwargs, False)._pipda_eval(
                        env
                    )
                )

            return func(*boundargs1.args, **boundargs1.kwargs)

        return (
            Function(func, args, kwargs)
            if env is NULL
            else Function(func, args, kwargs)._pipda_eval(env)
        )

    if boundargs1: # it is for sure regular call
        if _have_expr(rest_args, rest_kwargs):
            return (
                Function(func, rest_args, rest_kwargs)._pipda_eval(firstarg)
                if env is NULL
                else Function(func, args, kwargs, False)._pipda_eval(env)
            )

        return func(*boundargs1.args, **boundargs1.kwargs)

    if boundargs2: # it is for sure a piping call
        return (
            Function(func, args, kwargs)
            if env is NULL
            else Function(func, args, kwargs)._pipda_eval(env)
        )

    # let it raise the argument bind error
    raise first_bind_error

def _try_calling_no_dataarg(
        func: Callable,
        args: Tuple,
        kwargs: Mapping[str, Any],
        env: Any
) -> Any:
    """Try to call the function without data argument in different ways."""
    boundargs = bind_arguments(func, args, kwargs)
    if not _have_expr(args, kwargs):
        # now able to call regularly
        return func(*boundargs.args, **boundargs.kwargs)

    out = Function(func, args, kwargs, False)
    return out if env is NULL else out._pipda_eval(env)

def _strip_first_arg(
        args: Tuple,
        kwargs: Mapping[str, Any]
) -> Tuple[Any, Tuple, Mapping[str, Any]]:
    """Separate the first argument, which applies to the dispatcher,
    and the rest arguments.

    The first argument has to be specified in the first place, even specified
    with keyword argument.
    """
    if args:
        return args[0], args[1:], kwargs
    if kwargs:
        firstarg = NULL
        out_kwargs = {}
        for i, key in enumerate(kwargs):
            if i == 0:
                firstarg = kwargs[key]
            else:
                out_kwargs[key] = kwargs[key]
        return firstarg, args, out_kwargs
    return NULL, args, kwargs


def _register_func_no_dataarg(
        func: Callable,
        verb_arg_only: bool
) -> Callable:
    """Register functions without data as the first argument"""
    return _wrapping_no_dataarg(func, 'PlainFunction', verb_arg_only)

def _register_func_dataarg(
        types: Union[FunctionType, Type, Iterable[Type]],
        func: Callable,
        verb_arg_only: bool
) -> Callable:
    """Register functions with data as the first argument"""
    generic = _generializing(func, types)
    return _wrapping_dataarg(generic, 'Function', verb_arg_only)

def _is_expr(expr: Any) -> bool:
    """Check if an expression includes any Expression object"""
    if isinstance(expr, (list, tuple, set)):
        return any(_is_expr(elem) for elem in expr)

    if isinstance(expr, dict):
        return any(_is_expr(item) for item in expr.items())

    return isinstance(expr, Expression)

def _have_expr(args: Tuple[Any], kwargs: Mapping[str, Any]) -> bool:
    """Check if arg and kwargs have Expression object"""
    return any(_is_expr(arg) for arg in chain(args, kwargs.values()))

@lru_cache()
def _dispatchable(
        generic: Callable,
        type_firstarg: Type
) -> bool:
    """Check if a type can be dispatched"""
    return generic.dispatch(type_firstarg).__name__ != '_not_implemented'

def _match_secondarg(func: Callable) -> bool:
    """Check if a value can fit the second argument of a function"""
    signature = inspect.signature(func)
    parameters = list(signature.parameters.values())
    firsttype = parameters[0].annotation
    secondtype = parameters[1].annotation

    # singledispatch dispatching for type annotations yet
    # still need a better solution for this
    # firsttype is secondtype or firsttype in secondtype.__args__?
    # 3rd-party packages: pyre, etc?
    return firsttype is secondtype
    # if secondtype is inspect._empty:
    #     return True

    # The type annotation for the second argument could be too broad,
    # for example: def func(a: DataFrame, b: Any): ...
    # we don't want b to match the first value.

    # # https://stackoverflow.com/questions/55503673
    # # https://stackoverflow.com/questions/50563546
    # return type_checker(secondtype).is_typeof(value)


register_piping('>>')
register_operator(Operator)
register_verb.astnode_fail_warning = True
register_func.astnode_fail_warning = True
