"""Verb and function calling rules

Verb calling rules
1. data >> verb(...)
    [PIPING_VERB]
    First argument should not be passed, using the data
2. data >> other_verb(verb(...))
   other_verb(data, verb(...))
   registered_func(verb(...))
    [PIPING]
    Try using the first argument to evaluate (FastEvalVerb), if first argument
    is data. Otherwise, if it is Expression object, works as a non-data
    Function.
3. verb(...)
    Called independently. The verb will be called regularly anyway.
    The first argument will be used as data to evaluate the arguments
    if there are any Expression objects
4. verb(...) with DataEnv
    First argument should not be passed in, will use the DataEnv's data
    to evaluate the arguments

Data function calling rules
1. data >> verb(func(...)) or verb(data, func(...))
    First argument is not used. Will use data
2. func(...)
    Called independently. The function will be called regularly anyway.
    Similar as Verb calling rule, but first argument will not be used for
    evaluation
3. func(...) with DataEnv
    First argument not used, passed implicitly with DataEnv.

Non-data function calling rules:
1. data >> verb(func(...)) or verb(data, func(...))
    Return a Function object waiting for evaluation
2. func(...)
    Called regularly anyway
3. func(...) with DataEnv
    Evaluate with DataEnv. For example: mean(f.x)
"""

from typing import Any, Callable

from .function import FastEvalFunction, Function
from .verb import Verb, FastEvalVerb


def verb_calling_rule1(
    generic: Callable,
    args: Any,
    kwargs: Any,
    envdata: Any,
) -> Any:
    """Verb calling rule #1

    >>> data >> verb(...)
    """
    return Verb(generic, args, kwargs)


def verb_calling_rule2(
    generic: Callable,
    args: Any,
    kwargs: Any,
    envdata: Any,
) -> Any:
    """Verb calling rule #2

    >>> data >> other_verb(verb(...))
    >>> other_verb(data, verb(...))
    >>> registered_func(verb(...))
    """
    # Try using the first argument
    # Evaluation triggered by other verb or function
    return FastEvalVerb(generic, args, kwargs)._pipda_fast_eval()


def verb_calling_rule3(
    generic: Callable,
    args: Any,
    kwargs: Any,
    envdata: Any,
) -> Any:
    """Verb calling rule #3

    >>> verb(...)
    """
    # Try using the first argument
    out = FastEvalVerb(generic, args, kwargs)._pipda_fast_eval()
    if isinstance(out, Function):
        # Let generic raise NotImplementedError
        return generic(*args, **kwargs)
    return out


def verb_calling_rule4(
    generic: Callable, args: Any, kwargs: Any, envdata: Any
) -> Any:
    """Verb calling rule #4

    >>> _ = DataEnv(...)
    >>> verb(...)
    """
    # use the envdata to evaluate
    return Verb(generic, args, kwargs)._pipda_eval(envdata)


def dfunc_calling_rule1(
    generic: Callable,
    args: Any,
    kwargs: Any,
    envdata: Any,
    verb_arg_only: bool,  # NULL
) -> Any:
    """Data function calling rule #1

    >>> data >> verb(func(...))
    >>> verb(data, func(...))
    """
    return Function(generic, args, kwargs)


def dfunc_calling_rule2(
    generic: Callable,
    args: Any,
    kwargs: Any,
    envdata: Any,
    verb_arg_only: bool,  # NULL
) -> Any:
    """Data function calling rule #2

    >>> func(...)
    """
    if verb_arg_only:
        raise ValueError(
            f"`{generic.__qualname__}` must only be used inside verbs."
        )

    return generic(*args, **kwargs)


def dfunc_calling_rule3(
    generic: Callable,
    args: Any,
    kwargs: Any,
    envdata: Any,  # Not NULL
    verb_arg_only: bool,
) -> Any:
    """Data function calling rule #3

    >>> _ = DataEnv(...)
    >>> func(...)
    """
    if verb_arg_only:
        raise ValueError(
            f"`{generic.__qualname__}` must only be used inside verbs."
        )
    return Function(generic, args, kwargs)._pipda_eval(envdata)


def ndfunc_calling_rule1(
    generic: Callable, args: Any, kwargs: Any, envdata: Any, verb_arg_only: bool
) -> Any:
    """Non-data function calling rule #1

    >>> data >> verb(func(...))
    """

    return FastEvalFunction(generic, args, kwargs, False)._pipda_fast_eval()


def ndfunc_calling_rule2(
    generic: Callable,
    args: Any,
    kwargs: Any,
    envdata: Any,
    verb_arg_only: bool,  # NULL
) -> Any:
    """Non-data function calling rule #2

    >>> func(...)
    """
    if verb_arg_only:
        raise ValueError(
            f"`{generic.__qualname__}` must only be used inside verbs."
        )
    return generic(*args, **kwargs)


def ndfunc_calling_rule3(
    generic: Callable,
    args: Any,
    kwargs: Any,
    envdata: Any,  # Not NULL
    verb_arg_only: bool,
) -> Any:
    """Non-data function calling rule #3

    >>> _ = DataEnv(...)
    >>> func(...)
    """
    if verb_arg_only:
        raise ValueError(
            f"`{generic.__qualname__}` must only be used inside verbs."
        )
    return Function(generic, args, kwargs, False)._pipda_eval(envdata)
