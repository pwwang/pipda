"""Provide definition for functions that used as verb arguments"""
from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, List, TYPE_CHECKING, Sequence, Set, Type
from functools import singledispatch, update_wrapper

from .utils import evaluate_expr, has_expr, update_user_wrapper, is_piping
from .expression import Expression

if TYPE_CHECKING:
    from inspect import BoundArguments
    from .context import ContextType
    from .verb import Verb


class FunctionCall(Expression):
    """A function call object that awaits for evaluation

    Args:
        func: A registered function by `register_func` or an expression,
            for example, `f.col.mean`
        args: and
        kwargs: The arguments for the function
    """

    def __init__(
        self,
        func: Function | Verb | Expression,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._pipda_func = func
        self._pipda_args = args
        self._pipda_kwargs = kwargs

    def __str__(self) -> str:
        """Representation of the function call"""
        strargs: List[str] = []
        funname = str(self._pipda_func)
        if self._pipda_args:
            strargs.extend((str(arg) for arg in self._pipda_args))
        if self._pipda_kwargs:
            strargs.extend(
                f"{key}={val}" for key, val in self._pipda_kwargs.items()
            )
        return f"{funname}({', '.join(strargs)})"

    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        """Evaluate the function call"""
        func = self._pipda_func
        args = [evaluate_expr(arg, data, context) for arg in self._pipda_args]
        kwargs = {
            key: evaluate_expr(val, data, context)
            for key, val in self._pipda_kwargs.items()
        }

        if isinstance(func, Expression):
            # f.a(1)
            func = evaluate_expr(func, data, context)

        if not isinstance(func, Function):
            return func(*args, **kwargs)

        if not args and not kwargs:
            return func.func()

        if func.dispatchable:
            for t, fun in reversed(func.registry.items()):
                if t is object:
                    continue
                if (
                    any(isinstance(arg, t) for arg in args)
                    or any(isinstance(val, t) for val in kwargs.values())
                ):
                    return fun(*args, **kwargs)

        return func.func(*args, **kwargs)


class PipeableFunctionCall(FunctionCall):

    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        func = self._pipda_func
        args = [evaluate_expr(arg, data, context) for arg in self._pipda_args]
        kwargs = {
            key: evaluate_expr(val, data, context)
            for key, val in self._pipda_kwargs.items()
        }

        if not isinstance(func, Function):
            return func(data, *args, **kwargs)

        if func.dispatchable:
            for t, fun in reversed(func.registry.items()):
                if t is object:
                    continue
                if (
                    isinstance(data, t)
                    or any(isinstance(arg, t) for arg in args)
                    or any(isinstance(val, t) for val in kwargs.values())
                ):
                    return fun(data, *args, **kwargs)

        return func.func(data, *args, **kwargs)


class Registered(ABC):
    """Base function for registered function/verb"""

    def __str__(self):
        """Used to stringify the whole expression"""
        return self.func.__name__

    @property
    def signature(self):
        # cached property returns None for numpy.vectorize() object
        if not self._signature:
            self._signature = inspect.signature(self.func)
        return self._signature

    def bind_arguments(self, *args, **kwargs: Any) -> BoundArguments:
        boundargs = self.signature.bind(*args, **kwargs)
        boundargs.apply_defaults()
        return boundargs

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call a registered function/verb"""


class Function(Registered):
    """Registered function

    Args:
        func: The original function
        context: The context
        extra_context: The extra context for keyword arguments
    """

    def __init__(
        self,
        func: Callable,
        name: str = None,
        qualname: str = None,
        doc: str = None,
        module: str = None,
        signature: inspect.Signature = None,
        dispatchable: str | Set[str] = None,
    ) -> None:
        self._signature = signature
        self.dispatchable = dispatchable

        update_wrapper(self, func)
        update_user_wrapper(
            self,
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
        )

        if self.dispatchable:

            @singledispatch
            def _func(*args, **kwargs):
                return func(*args, **kwargs)

            self.func = _func  # type: ignore
            self.registry = _func.registry
            self.dispatch = _func.dispatch
        else:
            self.func = func  # type: ignore

    def register(
        self,
        types: Type | Sequence[Type],
    ) -> Callable[[Callable], Function]:
        """Register a function for a type"""
        if not self.dispatchable:
            raise ValueError("Function is not dispatchable")

        if not isinstance(types, (list, tuple, set)):
            types = [types]  # type: ignore [list-item]

        def _register(func):
            for t in types:
                self.func.register(t, func)
            return self

        return _register

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call a registered function"""
        if not args and not kwargs:
            return self.func()

        if not has_expr(args) and not has_expr(kwargs):
            if self.dispatchable:
                for t, fun in reversed(self.registry.items()):
                    if t is object:
                        continue
                    if (
                        any(isinstance(arg, t) for arg in args)
                        or any(isinstance(val, t) for val in kwargs.values())
                    ):
                        return fun(*args, **kwargs)
            return self.func(*args, **kwargs)

        return FunctionCall(self, *args, **kwargs)


class PipeableFunction(Function):
    def __init__(
        self,
        func: Callable,
        name: str = None,
        qualname: str = None,
        doc: str = None,
        module: str = None,
        signature: inspect.Signature = None,
        ast_fallback: str = "normal_warning",
        dispatchable: str | Set[str] = None,
    ) -> None:
        super().__init__(
            func,
            name,
            qualname,
            doc,
            module,
            signature,
            dispatchable,
        )
        self.ast_fallback = ast_fallback

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call a registered pipeable function"""
        ast_fallback = kwargs.pop("__ast_fallback", self.ast_fallback)

        if is_piping(self.func.__name__, ast_fallback):
            return PipeableFunctionCall(self, *args, **kwargs)

        return super().__call__(*args, **kwargs)


def register_func(
    func: Callable = None,
    *,
    name: str = None,
    qualname: str = None,
    doc: str = None,
    module: str = None,
    signature: inspect.Signature = None,
    pipeable: bool = False,
    ast_fallback: str = "normal_warning",
    dispatchable: str | Set[str] = None,
    funclass: Type[Function] = None,
) -> Function | Callable:
    """Register a function to be used as a verb argument so that they don't
    get evaluated immediately

    Args:
        func: The original function
        name: and
        qualname: and
        doc: and
        module: and
        signature: The meta information about the function to overwrite `func`'s
            or when it's not available from `func`
        pipeable: Whether the function is pipeable
            If pipeable, `[1, 2, 3] >> sum()` is supported
        dispatchable: Whether the function is dispatchable, if so, it should
            be the name/names of the arguments that are used to detect the
            dispatched type.

    Returns:
        A registered `Function` object, or a decorator if `func` is not given
    """
    if func is None:
        return lambda fun: register_func(
            fun,
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
            signature=signature,
            pipeable=pipeable,
            dispatchable=dispatchable,
            funclass=funclass,
        )

    if pipeable:
        funclass = funclass or PipeableFunction
        return funclass(  # type: ignore
            func,
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
            signature=signature,
            ast_fallback=ast_fallback,
            dispatchable=dispatchable,
        )

    funclass = funclass or Function
    return Function(
        func,
        name=name,
        qualname=qualname,
        doc=doc,
        module=module,
        signature=signature,
        dispatchable=dispatchable,
    )
