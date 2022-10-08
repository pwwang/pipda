"""Provide verb definition"""
from __future__ import annotations

from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Sequence,
    Type,
)
from functools import singledispatch, update_wrapper

from .utils import (
    has_expr,
    evaluate_expr,
    is_piping_verbcall,
    update_user_wrapper,
)
from .context import ContextPending
from .expression import Expression
from .function import FunctionCall, Registered

if TYPE_CHECKING:
    from inspect import Signature
    from .context import ContextType


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
        strargs: List[str] = []
        if not self._pipda_func.dep:
            strargs.append(".")

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
        context = (
            self._pipda_func.contexts.get(func, None)
            or self._pipda_func.contexts["_"]
            or context
        )

        if isinstance(context, Enum):
            context = context.value
        if isinstance(context, ContextPending):
            return func(data, *self._pipda_args, **self._pipda_kwargs)

        extra_contexts = (
            self._pipda_func.extra_contexts.get(func, None)
            or self._pipda_func.extra_contexts["_"]
        )
        if extra_contexts:
            bound = self._pipda_func.bind_arguments(
                data,
                *self._pipda_args,
                **self._pipda_kwargs,
            )
            for key, val in bound.arguments.items():
                ctx = extra_contexts.get(key, context)
                val = evaluate_expr(val, data, ctx)
                bound.arguments[key] = val

            return func(*bound.args, **bound.kwargs)

        # we don't need signature if there is no extra context
        return func(
            data,
            *(evaluate_expr(arg, data, context) for arg in self._pipda_args),
            **{
                key: evaluate_expr(val, data, context)
                for key, val in self._pipda_kwargs.items()
            },
        )


class Verb(Registered):
    """The registered verb"""

    def __init__(
        self,
        func: Callable,
        types: Type | Sequence[Type],
        context: ContextType,
        extra_contexts: Mapping[str, ContextType],
        name: str,
        qualname: str,
        doc: str,
        module: str,
        signature: Signature,
        dep: bool,
        ast_fallback: str,
    ) -> None:
        self.dep = dep
        self.ast_fallback = ast_fallback

        self.contexts: Dict[str | Callable, ContextType] = {"_": context}
        self.extra_contexts: Dict[str | Callable, Mapping[str, ContextType]] = {
            "_": extra_contexts
        }

        if types is None:
            # used to check if types are registered
            self._generic = func
        else:
            def generic(__data, *args, **kwargs):
                raise NotImplementedError(
                    f"[{func.__name__}] Type `{type(__data).__name__}` "
                    "is not registered."
                )
            self._generic = generic

        wrapped = singledispatch(self._generic)
        update_wrapper(self, func)
        update_wrapper(wrapped, func)
        update_user_wrapper(
            self,
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
        )
        update_user_wrapper(
            wrapped,
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
        )

        if types is not None:
            for t in types:
                wrapped.register(t, func)

        self.func = wrapped
        self.registry = wrapped.registry
        self.dispatch = wrapped.dispatch
        self._signature = signature

    def register(
        self,
        types: Type | Sequence[Type],
        context: ContextType = None,
        extra_contexts: Mapping[str, ContextType] = None,
    ) -> Callable[[Callable], Verb]:
        """Register for other types"""
        if not isinstance(types, (list, tuple, set)):
            types = [types]  # type: ignore [list-item]

        def decor(fun: Callable) -> Verb:
            self.contexts[fun] = context
            self.extra_contexts[fun] = extra_contexts or {}
            for t in types:
                self.func.register(t, fun)
            return self

        return decor

    def registered(self, cls: Type) -> bool:
        """Check if a type is registered"""
        return self.dispatch(cls) is not self._generic

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

        ast_fallback = kwargs.pop("__ast_fallback", self.ast_fallback)

        if is_piping_verbcall(self.func.__name__, ast_fallback):
            # data >> verb(...)
            return VerbCall(self, *args, **kwargs)

        if len(args) == 0:
            raise TypeError(f"{self.__name__}() missing at least one argument.")

        data, *args = args
        if has_expr(data):
            return FunctionCall(self, data, *args, **kwargs)

        return VerbCall(self, *args, **kwargs)._pipda_eval(data)


def register_verb(
    types: Type | Sequence[Type],
    *,
    context: ContextType = None,
    extra_contexts: Mapping[str, ContextType] = None,
    name: str = None,
    qualname: str = None,
    doc: str = None,
    module: str = None,
    signature: Signature = None,
    dep: bool = False,
    ast_fallback: str = "normal_warning",
    func: Callable = None,
) -> Callable[[Callable], Verb] | Verb:
    """Register a verb

    Args:
        types: The types of the data allowed to pipe in
            If `None`, then `func` is a generic function instead of an
            automatically created one to raise `NotImplementedError` by default
        context: The context to evaluate the arguments
        extra_contexts: Extra contexts to evaluate the keyword arguments
        name: and
        qualname: and
        doc: and
        module: and
        signature: The meta information about the function to overwrite `func`'s
            or when it's not available from `func`
        dep: Whether the verb is dependent.
            >>> @register_func([1, 2], context=Context.EVAL, dep=True)
            >>> def length(data):
            >>>     return len(data)
            >>> # with dep=True
            >>> # length()  -> VerbCall
            >>> # with dep=False
            >>> # length()  -> TypeError, argument data is missing
        ast_fallback: What's the supposed way to call the verb when
            AST node detection fails.
            piping - Suppose this verb is called like `data >> verb(...)`
            normal - Suppose this verb is called like `verb(data, ...)`
            piping_warning - Suppose piping call, but show a warning
            normal_warning - Suppose normal call, but show a warning
            raise - Raise an error
        func: The function works as a verb.
    """
    if func is None:
        return lambda fun: register_verb(  # type: ignore
            types=types,
            context=context,
            extra_contexts=extra_contexts or {},
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
            signature=signature,
            dep=dep,
            ast_fallback=ast_fallback,
            func=fun,
        )

    if types is not None and not isinstance(types, (list, tuple, set)):
        types = [types]  # type: ignore [list-item]

    return Verb(
        func,
        types=types,
        context=context,
        extra_contexts=extra_contexts or {},
        name=name,
        qualname=qualname,
        doc=doc,
        module=module,
        signature=signature,
        dep=dep,
        ast_fallback=ast_fallback,
    )
