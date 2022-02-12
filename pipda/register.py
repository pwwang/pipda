"""Provide register_* suite"""
import ast
import sys
from collections import namedtuple
from enum import Enum
from functools import singledispatch, wraps
from types import FunctionType
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
)

from .context import ContextAnnoType, ContextBase
from .operator import Operator
from .utils import NULL, CallingEnvs, calling_env, get_env_data
from .verb import Verb
from ._calling import (
    verb_calling_rule1,
    verb_calling_rule2,
    verb_calling_rule3,
    verb_calling_rule4,
    dfunc_calling_rule1,
    dfunc_calling_rule2,
    dfunc_calling_rule3,
    ndfunc_calling_rule1,
    ndfunc_calling_rule2,
    ndfunc_calling_rule3,
)

# The Sign tuple
Sign = namedtuple("Sign", ["method", "token"])

# All supported signs
#   method is used to be attached to verbs
#   ast token class is used to check if the verb or function
#       is running in piping mode
PIPING_SIGNS = {
    "+": Sign("__radd__", ast.Add),
    "-": Sign("__rsub__", ast.Sub),
    "*": Sign("__rmul__", ast.Mult),
    "@": Sign("__rmatmul__", ast.MatMult),
    "/": Sign("__rtruediv__", ast.Div),
    "//": Sign("__rfloordiv__", ast.FloorDiv),
    "%": Sign("__rmod__", ast.Mod),
    "**": Sign("__rpow__", ast.Pow),
    "<<": Sign("__rlshift__", ast.LShift),
    ">>": Sign("__rrshift__", ast.RShift),
    "&": Sign("__rand__", ast.BitAnd),
    "^": Sign("__rxor__", ast.BitXor),
    "|": Sign("__ror__", ast.BitOr),
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
    **attrs: Any,
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

    Verb calling rules
    1. data >> verb(...)
       First argument should not be passed, using the data
    2. data >> other_verb(verb(...))
       First argument used, and a Function object will be returned
       from the verb. `f` represents the data, instead of the first argument
       of the verb.
    3. verb(...)
       Called independently. The verb will be called regularly anyway.
       The first argument will be used as data to evaluate the arguments
       if there are any Expression objects
    4. verb(...) with DataEnv
       First argument should not be passed in, will use the DataEnv's data
       to evaluate the arguments

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
        types, context, func, extra_contexts
    )

    if func is None:
        return lambda fun: register_verb(
            types, context, fun, extra_contexts, **attrs
        )

    if types is None:
        raise ValueError(
            "Verbs must be registered with data argument "
            "(`types` cannot be None)"
        )

    for name, attr in attrs.items():
        setattr(func, name, attr)

    # allow register to have different context
    func.context = context
    func.extra_contexts = extra_contexts

    generic = _generalizing(func, types)
    return _wrapping_verb(generic)


def register_func(
    types: Union[FunctionType, Type, Iterable[Type]] = object,
    context: Optional[ContextAnnoType] = None,
    func: Optional[FunctionType] = None,
    verb_arg_only: bool = False,
    extra_contexts: Optional[Mapping[str, ContextAnnoType]] = None,
    **attrs: Any,
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

    Data function calling rules
    1. data >> verb(func(...))
       First argument is not used. Will use data
    2. func(...)
       Called independently. The function will be called regularly anyway.
       Similar as Verb calling rule, but first argument will not be used for
       evaluation
    3. func(...) with DataEnv
       First argument not used, passed implicitly with DataEnv.

    Non-data function calling rules:
    1. data >> verb(func(...))
       Return a Function object waiting for evaluation
    2. func(...)
       Called regularly anyway
    3. func(...) with DataEnv
       Evaluate with DataEnv. For example: mean(f.x)

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
        types, context, func, extra_contexts
    )

    if func is None:
        return lambda fun: register_func(
            types, context, fun, verb_arg_only, extra_contexts, **attrs
        )

    for name, attr in attrs.items():
        setattr(func, name, attr)

    # allow register to have different context
    func.context = context
    func.extra_contexts = extra_contexts

    if types is None:
        return _register_ndfunc(func, verb_arg_only)

    return _register_dfunc(types, func, verb_arg_only)


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
    origfunc = getattr(func, "__origfunc__", None)
    if origfunc is None:
        raise ValueError(f"Function is not registered with pipda: {func}")
    return origfunc


# Helper functions --------------------------------


def _clean_register_args(
    types: Optional[Union[FunctionType, Type, Iterable[Type]]],
    context: Optional[ContextAnnoType],
    func: Optional[Callable],
    extra_contexts: Optional[Mapping[str, ContextAnnoType]],
) -> Tuple[
    Optional[Iterable[Type]],
    Optional[ContextBase],
    Optional[Callable],
    Optional[Mapping[str, ContextBase]],
]:
    """Clean up the register_* arguments and get the right order"""
    if func is None and isinstance(types, FunctionType):
        func, types = types, object

    if types is not None and not isinstance(types, (tuple, set, list)):
        types = (types,)  # type: ignore

    if isinstance(context, Enum):
        context = context.value

    extra_contexts = extra_contexts or {}
    extra_contexts = {
        key: ctx.value if isinstance(ctx, Enum) else ctx
        for key, ctx in extra_contexts.items()
    }

    return types, context, func, extra_contexts  # type: ignore


def _generalizing(func: Callable, types: Iterable[Type]) -> Callable:
    """Returns the generic function and register the types"""
    if object in types:
        generic = singledispatch(func)
    else:
        # have to define this function here, so that every time a new function
        # is generated.
        # Otherwise, singledispatch mixed the registry when registering the
        # same function
        @wraps(func)
        def _not_implemented(_data: Any, *args: Any, **kwargs: Any) -> None:
            raise NotImplementedError(
                f"{func.__qualname__!r} is not "
                f"registered for type: {type(_data)}."
            )

        _not_implemented.__name__ = "_not_implemented"
        # __name__ is used to tell if object is allowed
        _not_implemented.context = func.context
        _not_implemented.extra_contexts = func.extra_contexts
        generic = singledispatch(_not_implemented)

    for typ in types:
        if typ is not object:
            generic.register(typ, func)

    generic.__origfunc__ = func
    return generic


def _wrapping_verb(generic: Callable) -> Callable:
    """Wrapping the generic function with data argument
    This basically defines how to run the function
    """

    @wraps(generic.__origfunc__)  # type: ignore
    def wrapper(
        *args: Any,
        __calling_env: Optional[CallingEnvs] = None,
        __envdata: Any = NULL,
        **kwargs: Any,
    ) -> Any:
        """The wrapper that eventually runs

        Args:
            *args: and
            **kwargs: The arguments passed to the original function
            __calling_env: The calling environment. Mostly used for debugging
                Will detect from the AST.
            __envdata: The environment data for evaluating the Expression
                object
        """
        call_env = __calling_env or calling_env('Verb')

        envdata = NULL
        if call_env is CallingEnvs.PIPING_VERB:
            calling_rule = verb_calling_rule1
        elif call_env is CallingEnvs.PIPING:
            calling_rule = verb_calling_rule2
        else:
            envdata = (
                __envdata
                if __envdata is not NULL
                else get_env_data(sys._getframe(1))
            )

            calling_rule = (
                verb_calling_rule3 if envdata is NULL else verb_calling_rule4
            )

        return calling_rule(generic, args, kwargs, envdata)

    wrapper.register = _singledispatch_register(generic)
    wrapper.registry = generic.registry
    wrapper.dispatch = generic.dispatch
    wrapper.__pipda__ = "Verb"
    wrapper.__origfunc__ = generic.__origfunc__

    return wrapper


def _wrapping_dfunc(
    generic: Callable, verb_arg_only: Optional[bool] = None
) -> Callable:
    """Wrapping the generic function with data argument
    This basically defines how to run the function
    """

    @wraps(generic.__origfunc__)  # type: ignore
    def wrapper(
        *args: Any,
        __calling_env: Optional[CallingEnvs] = None,
        __envdata: Any = NULL,
        **kwargs: Any,
    ) -> Any:
        """The wrapper that eventually runs

        Args:
            *args: and
            **kwargs: The arguments passed to the original function
            __calling_env: The calling environment. Mostly used for debugging
                Will detect from the AST.
            __envdata: The environment data for evaluating the Expression
                object
        """
        call_env = __calling_env or calling_env('Function')

        if call_env is CallingEnvs.PIPING:
            calling_rule = dfunc_calling_rule1
            envdata = NULL
        else:
            envdata = (
                __envdata
                if __envdata is not NULL
                else get_env_data(sys._getframe(1))
            )
            calling_rule = (
                dfunc_calling_rule2 if envdata is NULL else dfunc_calling_rule3
            )

        return calling_rule(generic, args, kwargs, envdata, verb_arg_only)

    wrapper.register = _singledispatch_register(generic)
    wrapper.registry = generic.registry
    wrapper.dispatch = generic.dispatch
    wrapper.__pipda__ = "Function"
    wrapper.__origfunc__ = generic.__origfunc__

    return wrapper


def _wrapping_ndfunc(
    generic: Callable, verb_arg_only: Optional[bool] = None
) -> Callable:
    """Wrapping the generic function without data argument"""

    @wraps(generic)  # type: ignore
    def wrapper(
        *args: Any,
        __calling_env: Any = None,
        __envdata: Any = NULL,  # could be None
        **kwargs: Any,
    ) -> Any:
        call_env = __calling_env or calling_env('PlainFunction')

        # As argument of a verb
        if call_env is CallingEnvs.PIPING:
            calling_rule = ndfunc_calling_rule1
            envdata = NULL
        else:
            envdata = (
                __envdata
                if __envdata is not NULL
                else get_env_data(sys._getframe(1))
            )

            calling_rule = (
                ndfunc_calling_rule2
                if envdata is NULL
                else ndfunc_calling_rule3
            )

        return calling_rule(generic, args, kwargs, envdata, verb_arg_only)

    wrapper.__pipda__ = "PlainFunction"
    wrapper.__origfunc__ = generic
    return wrapper


def _singledispatch_register(
    generic: Callable,
) -> Callable[[Union[Type, Iterable[Type]], Any, Optional[Callable]], Callable]:
    """Allow register of generic function to register types with context"""

    def _register_func(
        types: Union[Type, Iterable[Type]],
        context: Optional[ContextAnnoType] = None,
        func: Optional[Callable] = None,
        # extra_contexts?
    ) -> Callable:
        types, context, func, _ = _clean_register_args(
            types, context, func, None
        )

        if func is None:
            return lambda fun: _register_func(types, context, fun)

        func.context = context
        out = func
        for typ in types:
            out = generic.register(typ, out)
            # don't use functools.wraps() as it will override func.context
            out.__name__ = generic.__origfunc__.__name__
            out.__qualname__ = generic.__origfunc__.__qualname__
            out.__doc__ = generic.__origfunc__.__doc__
        return out

    return _register_func


def _register_ndfunc(func: Callable, verb_arg_only: bool) -> Callable:
    """Register functions without data as the first argument"""
    return _wrapping_ndfunc(func, verb_arg_only)


def _register_dfunc(
    types: Iterable[Type], func: Callable, verb_arg_only: bool
) -> Callable:
    """Register functions with data as the first argument"""
    generic = _generalizing(func, types)
    return _wrapping_dfunc(generic, verb_arg_only)


register_piping(">>")
register_operator(Operator)
