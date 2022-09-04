"""Provide verb definition"""
from __future__ import annotations

import ast
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, List, Mapping, Sequence, Type
from functools import singledispatch, update_wrapper

from .utils import evaluate_expr, is_piping_verbcall
from .context import ContextPending
from .expression import Expression
from .function import Registered, Function

if TYPE_CHECKING:
    from .context import ContextType

PIPING_OPS = {
    ">>": ("__rrshift__", ast.RShift),
    "|": ("__ror__", ast.BitOr),
    "//": ("__rfloordiv__", ast.FloorDiv),
    "@": ("__rmatmul__", ast.MatMult),
    "%": ("__rmod__", ast.Mod),
    "&": ("__rand__", ast.BitAnd),
    "^": ("__rxor__", ast.BitXor),
}


class VerbCall(Expression):
    """A verb call

    Args:
        func: The registered verb
        args: and
        kwargs: The arguments for the verb
    """
    PIPING: str = None

    def __init__(
        self,
        func: Verb,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._pipda_func = func
        self._pipda_args = args
        self._pipda_kwargs = kwargs

    def __str__(self) -> str:
        if not self._pipda_func.dep:
            strargs: List[str] = ["."]

        funname = str(self._pipda_func)
        if self._pipda_args:
            strargs.extend((str(arg) for arg in self._pipda_args))
        if self._pipda_kwargs:
            strargs.extend(
                f"{key}={val}" for key, val in self._pipda_kwargs.items()
            )
        return f"{funname}({', '.join(strargs)})"

    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        func = self._pipda_func.dispatch(type(data))
        context = func.context or self._pipda_func.context or context

        if isinstance(context, Enum):
            context = context.value
        if isinstance(context, ContextPending):
            return func(data, *self._pipda_args, **self._pipda_kwargs)

        extra_contexts = func.extra_contexts or self._pipda_func.extra_contexts

        args = (evaluate_expr(arg, data, context) for arg in self._pipda_args)
        kwargs = {
            key: evaluate_expr(
                val,
                data,
                extra_contexts.get(key, context)
            )
            for key, val in self._pipda_kwargs.items()
        }
        return func(data, *args, **kwargs)


class Verb(Registered):
    """The registered verb"""

    def __init__(
        self,
        func: Callable,
        types: Type | Sequence[Type],
        context: ContextType,
        extra_contexts: Mapping[str, ContextType],
        dep: bool,
        expr_as_data: bool,
        ast_fallback: str,
        ast_fallback_arg: bool,
    ) -> None:
        self.dep = dep
        self.expr_as_data = expr_as_data
        self.ast_fallback = ast_fallback
        self.ast_fallback_arg = ast_fallback_arg

        def fallback(_data, *args, **kwargs):
            raise NotImplementedError(
                f"[{func.__name__}] Type `{type(_data).__name__}` "
                "is not registered."
            )
        # used to check if types are registered
        fallback.context = context
        fallback.extra_contexts = extra_contexts

        fallback = singledispatch(fallback)
        update_wrapper(self, func)
        update_wrapper(fallback, func)

        func.context = context
        func.extra_contexts = extra_contexts
        for t in types:
            fallback.register(t, func)

        self.func = fallback
        self.registry = fallback.registry
        self.dispatch = fallback.dispatch
        # default contexts
        self.context = context
        self.extra_contexts = extra_contexts
        self._signature = None

    def register(
        self,
        types: Type | Sequence[Type],
        context: ContextType = None,
        extra_contexts: Mapping[str, ContextType] = None,
    ) -> Callable[[Callable], Verb]:
        if not isinstance(types, Sequence):
            types = [types]

        def decor(fun: Callable) -> Verb:
            fun.context = context
            fun.extra_contexts = extra_contexts or {}
            for t in types:
                self.func.register(t, fun)
            return self

        return decor

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """How should we call the function

        1. The first argument is the data, which will be used to
            evaluate other arguments
            The verb is called like `verb(...)`
        2. It calls into a VerbCall object awaiting future data to evaluate
            The verb is called like `data >> verb(...)`

        Check the AST node to see if it is called: `data >> verb(...)`
        If `self.dep` is True, only 2 is allowed.
        """
        if self.dep:
            # Meaning data should never be passed explictly
            return VerbCall(self, *args, **kwargs)

        if self.ast_fallback_arg:
            ast_fallback = kwargs.pop("__ast_fallback", self.ast_fallback)
        else:
            ast_fallback = self.ast_fallback

        if is_piping_verbcall(self.func.__name__, ast_fallback):
            # data >> verb(...)
            return VerbCall(self, *args, **kwargs)

        bound = self.bind_arguments(*args, **kwargs)
        data, *args = bound.args

        call = VerbCall(self, *args, **bound.kwargs)
        if not isinstance(data, Expression) or not self.expr_as_data:
            # Use the registered context
            return call._pipda_eval(data)

        # evaluate the data first so that the symbolics in the arguments
        # refer to the evaluated data
        return Function(
            lambda dat: call._pipda_eval(dat),
            context=None,
            extra_contexts={}
        )(data)


def register_verb(
    types: Type | Sequence[Type],
    *,
    context: ContextType = None,
    extra_contexts: Mapping[str, ContextType] = None,
    dep: bool = False,
    expr_as_data: bool = True,
    ast_fallback: str = "normal_warning",
    ast_fallback_arg: bool = False,
) -> Callable[[Callable], Verb]:
    """Register a verb

    Args:
        types: The types of the data allowed to pipe in
        context: The context to evaluate the arguments
        extra_contexts: Extra contexts to evaluate the keyword arguments
            Those should be keyword-only arguments
        dep: Whether the verb is dependent.
            >>> @register_func([1, 2], context=Context.EVAL, dep=True)
            >>> def length(data):
            >>>     return len(data)
            >>> # with dep=True
            >>> # length()  -> VerbCall
            >>> # with dep=False
            >>> # length()  -> TypeError, argument data is missing
        expr_as_data: Whether to allow Expression object as data to pipe in
            So we could do `data >> bind_rows(head(f), tail(f))`
        ast_fallback: What's the supposed way to call the verb when
            AST node detection fails.
            piping - Suppose this verb is called like `data >> verb(...)`
            normal - Suppose this verb is called like `verb(data, ...)`
            piping_warning - Suppose piping call, but show a warning
            normal_warning - Suppose normal call, but show a warning
            raise - Raise an error
        ast_fallback_arg - Whether to use `__ast_fallback` keyword argument
            to indicate one of the above behaviors
            If `__ast_fallback` is not provide, use value from `ast_fallback`
    """
    if not isinstance(types, Sequence):
        types = [types]

    return lambda fun: Verb(
        fun,
        types=types,
        context=context,
        extra_contexts=extra_contexts or {},
        dep=dep,
        expr_as_data=expr_as_data,
        ast_fallback=ast_fallback,
        ast_fallback_arg=ast_fallback_arg,
    )


def register_piping(op: str) -> None:
    """Register the piping operator for verbs

    Args:
        op: The operator used for piping
            Avaiable:  ">>", "|", "//", "@", "%", "&" and "^"
    """
    if op not in PIPING_OPS:
        raise ValueError(f"Unsupported piping operator: {op}")

    if VerbCall.PIPING:
        curr_method = PIPING_OPS[VerbCall.PIPING][0]
        delattr(VerbCall, curr_method)

    VerbCall.PIPING = op
    setattr(VerbCall, PIPING_OPS[op][0], VerbCall._pipda_eval)


register_piping(">>")
