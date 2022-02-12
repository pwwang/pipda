"""Provide utilities"""
import ast
import inspect
import sys
import warnings
from contextlib import contextmanager
from enum import Enum, auto
from functools import lru_cache, singledispatch
from types import FrameType
from typing import Any, Callable, Generator, Mapping, Tuple

from diot import Diot
from executing import Source
from pure_eval import CannotEval, Evaluator

from .context import ContextAnnoType

DATA_CONTEXTVAR_NAME = "__pipda_context_data__"

options = Diot(
    # Warn about failure to get ast node
    warn_astnode_failure=True,
    # All piping mode:
    # - Assume all verbs are using PIPING_VERB env
    # - Assume all data functions are using PIPING env
    # - Assume all non-data functions are using PIPING verbs
    # This is useful when source code is not available.
    assume_all_piping=False,
)


@contextmanager
def options_context(**kwargs: Mapping[str, Any]) -> Generator:
    """A context manager to execute code with temporary options"""
    tmp_opts = options.copy()
    options.update(**kwargs)
    yield
    options.update(tmp_opts)


class InaccessibleToNULLException(Exception):
    """Raises when access to NULLClass object"""


class NULLClass:
    """Sometimes, None is a valid option. In order to distinguish this
    situation, NULL is used for a default.

    It is also used as data to fast evaluate FastEvalFunction and FastEvalVerb
    objects. If failed, InaccessibleToNULLException will be raised.
    """

    def __repr__(self) -> str:
        """String representation"""
        return "NULL"

    def _inaccessible(self, *args: Any, **kwargs: Any) -> Any:
        raise InaccessibleToNULLException

    __bool__ = _inaccessible
    __len__ = _inaccessible
    __getitem__ = _inaccessible
    __getattr__ = _inaccessible
    # more ?


NULL = NULLClass()


class CallingEnvs(Enum):
    """Types of piping/calling envs"""

    # When a function works as an argument of a verb calling
    # data >> verb(func())
    #              ^^^^^^
    # Or
    # verb(data, func())
    #            ^^^^^^
    PIPING = auto()
    # When I am the verb in piping syntax
    # data >> verb(...)
    #         ^^^^^^^^^
    PIPING_VERB = auto()
    # # When I am an argument of any function not in a piping syntax
    # # func(x=func2())
    # #        ^^^^^^^
    # FUNC_ARG = auto()
    # Used to pass to the functions manually
    REGULAR = auto()


class DataEnv:
    """A data context that can be accessed by the function registered by
    `pipda.register_*` so that the data argument doesn't need to
    be passed when called

    Args:
        data: The data to be attached to the context
    """

    def __init__(self, data: Any, name: str = DATA_CONTEXTVAR_NAME) -> None:
        self.name = name
        self.data = data

    def get(self) -> Any:
        """Get the data"""
        return self.data

    def set(self, data: Any) -> None:
        """Update the data"""
        self.data = data

    def delete(self) -> None:
        """Delete the attached data"""
        self.set(NULL)


def get_env_data(frame: FrameType) -> Any:
    """Check and return if there is a data set in the context where
    the verb or function is called

    The data has to be named as `_`
    """
    envdata = frame.f_locals.get("_", None)
    if not isinstance(envdata, DataEnv) or envdata.name != DATA_CONTEXTVAR_NAME:
        return NULL
    return envdata.get()


def calling_env(funtype: str) -> Any:
    """Checking how the function is called:

    1. PIPING_VERB: It is a verb that is piped directed. ie. data >> verb(...)
    2. PIPING: It is a function called as (part of) the argument
        of a piping verb. ie.:

        >>> data >> verb(func(...))

        Note that `func` here could also be a verb. When a function is called
        inside a lambda body, it should not be counted in this situation:

        >>> data >> verb(lambda: func(...))

        In this case, func should be called as normal function.
        This function should return `None`
    3. FUNC_ARG: It is an argument of any function call
    4. None: None of the above situation fits

    This function should be only called inside register_*.wrapper
    """
    if options.assume_all_piping:
        return (
            CallingEnvs.PIPING_VERB
            if funtype == 'Verb'
            else CallingEnvs.PIPING
        )

    # frame 1: register_*.wrapper
    # frame 2: func(...)
    frame = sys._getframe(2)
    my_node = Source.executing(frame).node
    if not my_node and options.warn_astnode_failure:
        warnings.warn(
            "Failed to fetch the node calling the function, "
            "call it with the original function."
        )
        return None

    piping_verb_node = _get_piping_verb_node(my_node)
    if piping_verb_node is my_node and piping_verb_node is not None:
        return CallingEnvs.PIPING_VERB

    if _is_piping_verb_argument_node(my_node, piping_verb_node):
        return CallingEnvs.PIPING

    parent_call_node = _argument_node_of(my_node)
    if parent_call_node is None:
        return None

    # check if parent call node is a function registered by
    # register_verb/register_func
    evaluator = Evaluator.from_frame(frame)
    try:
        func = evaluator[parent_call_node.func]
    except CannotEval:  # pragma: no cover
        return None

    if functype(func) != "plain":
        return CallingEnvs.PIPING

    return None


def evaluate_expr(expr: Any, data: Any, context: ContextAnnoType) -> Any:
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


def functype(func: Callable) -> str:
    """Check the type of the function

    Args:
        func: A function

    Returns:
        The type of the function
        - verb: A verb that is registered by `register_verb`
        - func: A function that is registered by `register_func`, with
            data as the first argument
        - plain-func: A function that is registered by `register_func`,
            without data as the first argument
        - plain: A plain python function
    """
    pipda_type = getattr(func, "__pipda__", None)
    if pipda_type == "Verb":
        return "verb"
    if pipda_type == "Function":
        return "func"
    if pipda_type == "PlainFunction":
        return "plain-func"
    return "plain"


def bind_arguments(
    func: Callable,
    args: Tuple,
    kwargs: Mapping[str, Any],
    # type_check: bool = False,
    # ignore_first: bool = False,
    # ignore_types: Tuple[Type] = (Expression, )
) -> inspect.BoundArguments:
    """Try to bind arguments, instead of run the function to see if arguments
    can fit the function

    Args:
        func: The function
        args: The positional arguments to bind to the function
        kwargs: The keyword arguments to bind to the function
        type_check: Whether do the type check for the values
        ignore_first: Whether ignore type check for the first argument
        ignore_types: Types to be ignored (always return True for any values)

    Raises:
        TypeError: When arguments failed to bind or types of values
            don't match argument type annotations if `type_check` is True.

    Returns:
        inspect.BoundArguments
    """
    signature = inspect.signature(func)
    try:
        boundargs = signature.bind(*args, **kwargs)
    except TypeError as terr:
        raise TypeError(f"[{func.__qualname__}] {terr}") from None

    # if len(boundargs.arguments) > 0 and type_check:
    #     # some arguments bound
    #     firstarg = list(signature.parameters)[0]
    #     for key, val in boundargs.arguments.items():
    #         if ignore_first and key == firstarg:
    #             continue

    #         annotation = signature.parameters[key].annotation
    #         if annotation is inspect._empty:
    #             continue

    #         if not instanceof(val, annotation, ignore=ignore_types):
    #             raise TypeError(
    #                 f"[{func.__qualname__}] Argument `{key}` expect a value "
    #                 f"of {annotation}, got {val}"
    #             )

    boundargs.apply_defaults()
    return boundargs


# Helper functions -----------------------------


@lru_cache()
def _get_piping_verb_node(calling_node: ast.Call) -> ast.Call:
    """Get the ast node that is ensured the piping verb call

    Args:
        calling_node: Current Call node

    Returns:
        The verb call node if found, otherwise None
    """
    from .register import PIPING_SIGNS
    from .verb import Verb

    # check if we have the piping node (i.e. >>)
    child = calling_node
    parent = getattr(child, "parent", None)
    token = PIPING_SIGNS[Verb.CURRENT_SIGN].token
    while parent:
        if (
            # data >> verb(...)
            (isinstance(parent, ast.BinOp) and parent.right is child)
            # data >>= verb(...)
            or (isinstance(parent, ast.AugAssign) and parent.value is child)
        ) and isinstance(parent.op, token):
            return child

        child = parent
        parent = getattr(parent, "parent", None)
    return None


@lru_cache()
def _is_piping_verb_argument_node(
    sub_node: ast.Call, verb_node: ast.Call
) -> bool:
    """Check if node func() is an argument of verb() (i.e. verb(func()))"""
    if not verb_node:
        return False
    parent = sub_node
    while parent:
        if isinstance(parent, ast.Call) and (
            parent is verb_node or _argument_node_of(parent) is verb_node
        ):
            return True

        if isinstance(parent, ast.Lambda):
            # function inside lambda is not in a piping environment
            return False
        parent = getattr(parent, "parent", None)
    # when verb_node is ensured, we can anyway retrieve it as the parent of
    # sub_node
    return False  # pragma: no cover


@lru_cache()
def _argument_node_of(sub_node: ast.Call) -> ast.Call:
    """Get the Call node of a argument subnode"""
    parent = getattr(sub_node, "parent", None)
    while parent:
        if isinstance(parent, ast.Call) and (
            sub_node in parent.args or sub_node in parent.keywords
        ):
            return parent

        if isinstance(parent, ast.Lambda):
            # function inside lambda is not in a piping environment
            return None

        sub_node = parent
        parent = getattr(parent, "parent", None)
    return None
