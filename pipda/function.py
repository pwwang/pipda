from __future__ import annotations

import warnings
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Type
from types import MappingProxyType
from functools import singledispatch, update_wrapper

from .utils import (
    DEFAULT_BACKEND,
    MultiImplementationsWarning,
    TypeHolder,
    evaluate_expr,
    update_user_wrapper,
    has_expr,
    is_piping,
)
from .expression import Expression
from .piping import PipeableCall

if TYPE_CHECKING:
    from .context import ContextType


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
        func: Callable | Expression,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._pipda_func = func
        self._pipda_args = args
        self._pipda_kwargs = kwargs
        self._pipda_backend = kwargs.pop("__backend", None)

    def __str__(self) -> str:
        """Representation of the function call"""
        strargs: List[str] = []
        if isinstance(self._pipda_func, Expression):
            funname = str(self._pipda_func)
        else:
            funname = self._pipda_func.__name__

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

        functype = getattr(func, "_pipda_functype", None)
        if functype == "func":
            func = func.dispatch(backend=self._pipda_backend)
        elif functype == "dispatchable":
            func.dispatch(
                *(arg.__class__ for arg in args),
                backend=self._pipda_backend,
            )

        return func(*args, **kwargs)


class PipeableFunctionCall(FunctionCall, PipeableCall):
    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        """Evaluate the function call with the piped data

        Note that the piped data is the first argument, not the data from
        a verb that used to evaluate other expression arguments.
        """
        func = self._pipda_func
        args = (data, *self._pipda_args)
        if has_expr(args) or has_expr(self._pipda_kwargs):
            return FunctionCall(
                func,
                *args,
                **self._pipda_kwargs,
                __backend=self._pipda_backend,
            )

        functype = getattr(func, "_pipda_functype", None)
        if functype == "func":
            func = func.dispatch(backend=self._pipda_backend)  # type: ignore
        elif functype == "dispatchable":
            func.dispatch(  # type: ignore
                *(arg.__class__ for arg in args),
                backend=self._pipda_backend,
            )

        return func(*args, **self._pipda_kwargs)


def register_func(
    func: Callable = None,
    cls: Type = TypeHolder,
    *,
    plain: bool = False,
    name: str = None,
    qualname: str = None,
    doc: str = None,
    module: str = None,
    dispatchable: bool = False,
    pipeable: bool = False,
    ast_fallback: str = "normal_warning",
    ast_depth: int = 0,
) -> Callable:
    """Register a function

    A function, unlike a verb, is a function that doesn't evaluate its
    arguments by the first argument, which is the data, it depends on the
    data from a verb to evaluate the arguments if they are Expression objects.

    A function can also be defined as pipeable, so that the first argument
    can be piped in later.

    A function can also be defined as dispatchable. The types of any positional
    arguments are used to dispatch the implementation.

    Args:
        func: The generic function.
            If `None` (not provided), this function will return a decorator.
        cls: The default type to register for _default backend
            if TypeHolder, it is a generic function, and not counted as a
            real implementation.
            For plain or non-dispatchable functions, specify a different type
            than TypeHolder to indicate the func is a real implementation.
        plain: If True, the function will be registered as a plain function,
            which means it will be called without any evaluation of the
            arguments. It doesn't support dispatchable and pipeable.
        name: and
        qualname: and
        doc: and
        module: The meta information about the function to overwrite `func`'s
            or when it's not available from `func`
        ast_fallback: What's the supposed way to call the func when
            AST node detection fails.
            piping - Suppose this func is called like `data >> func(...)`
            normal - Suppose this func is called like `func(data, ...)`
            piping_warning - Suppose piping call, but show a warning
            normal_warning - Suppose normal call, but show a warning
            raise - Raise an error
        ast_depth: Whether this func is wrapped by other wrappers, if so,
            the depth should be provided to make the AST node detection

    Returns:
        The registered func or a decorator to register a func
    """
    if func is None:
        return lambda fun: register_func(
            fun,
            cls=cls,
            plain=plain,
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
            dispatchable=dispatchable,
            pipeable=pipeable,
            ast_fallback=ast_fallback,
            ast_depth=ast_depth,
        )

    if plain:
        # make sure the flags are correct
        dispatchable = pipeable = False

    def _backend_generic(*args, **kwargs):  # pyright: ignore
        raise NotImplementedError("Not implemented by the given backend.")

    if dispatchable:
        registry = OrderedDict(
            {
                DEFAULT_BACKEND: singledispatch(
                    func if cls is TypeHolder else _backend_generic
                )
            }
        )
    else:
        registry = OrderedDict({DEFAULT_BACKEND: func})  # type: ignore
    # backend => implementation
    favorables: Dict[str, Callable] = {}

    def dispatch(*clses, backend=None):
        """generic_func.dispatch(*clses, backend) -> <function impl>

        Runs the dispatch algorithm to return the best available implementation
        for the given *cls* registered on *generic_func* of given *backend*.

        If backend is not provided, we will look for the implementation of
        the backends in reverse order.

        The first cls can be dispatched is used.

        Args:
            clses: The types to dispatch
            backend: The backend to dispatch

        Returns:
            The implementation function
        """
        if not clses:
            clses = (object,)

        if backend is not None:
            try:
                reg = registry[backend]
            except KeyError:
                raise NotImplementedError(f"No such backend `{backend}`.")

            if not dispatchable:
                return reg

            for cl in clses:
                fun = reg.dispatch(cl)
                # Any impl found
                if fun is not _backend_generic:
                    return fun
            return _backend_generic

        impls = []
        favored_found = False
        for backend, reg in reversed(registry.items()):
            impl = None
            if not dispatchable:
                if (backend == DEFAULT_BACKEND and cls is TypeHolder) or (
                    favored_found and favorables.get(backend) is not reg
                ):
                    continue

                impl = reg
            else:
                for cl in clses:
                    fun = reg.dispatch(cl)
                    if (
                        # Not really an impl
                        fun is _backend_generic
                        or (
                            # The generic, supposed to raise NotImplementedError
                            fun is func
                            and cls is TypeHolder
                            and backend == DEFAULT_BACKEND
                        )
                        or (
                            # Non-favored impl after favored impl found
                            favored_found
                            and favorables.get(backend) is not fun
                        )
                    ):  # pragma: no cover
                        continue

                    impl = fun
                    break

            if impl is not None:
                if favorables.get(backend) is impl:
                    favored_found = True

                impls.append((backend, impl))

        if not impls:
            return func if cls is TypeHolder else _backend_generic

        if len(impls) > 1:
            warnings.warn(
                f"Multiple implementations found for `{wrapper.__name__}` "
                f"by backends: [{', '.join(impl[0] for impl in impls)}], "
                "register with more specific types, or pass "
                "`__backend=<backend>` to specify a backend.",
                MultiImplementationsWarning,
            )

        return impls[0][1]

    def register(cl=None, *, backend=DEFAULT_BACKEND, favored=False, fun=None):
        """generic_func.register(cl, backend, fun, favored) -> fun

        Args:
            cl: The type to register for the given backend
            backend: The backend to register for
            fun: The implementation function
            favored: Whether this implementation is favored. If so, non-favored
                implementations will be ignored if this implementation is found.

        Returns:
            The implementation function
        """
        if fun is None:
            return lambda fn: register(
                cl,
                backend=backend,
                favored=favored,
                fun=fn,
            )

        if not dispatchable:
            registry[backend] = fun
        else:
            if backend not in registry:
                registry[backend] = singledispatch(_backend_generic)

            registry[backend].register(cl, fun)

        if favored:
            favorables[backend] = fun
        return fun

    def wrapper(*args, **kwargs):
        if plain:
            backend = kwargs.pop("__backend", None)
            return dispatch(backend=backend)(*args, **kwargs)

        if pipeable:
            ast_fb = kwargs.pop("__ast_fallback", ast_fallback)

            if is_piping(wrapper.__name__, ast_fb, ast_depth):
                return PipeableFunctionCall(wrapper, *args, **kwargs)

        # Not pipeable
        if has_expr(args) or has_expr(kwargs):
            return FunctionCall(wrapper, *args, **kwargs)

        # No Expression objects, call directly
        backend = kwargs.pop("__backend", None)

        if dispatchable:
            func = dispatch(*(arg.__class__ for arg in args), backend=backend)
        else:
            func = dispatch(backend=backend)

        return func(*args, **kwargs)

    if plain:
        wrapper._pipda_functype = "plain"
    elif dispatchable:
        if cls is not TypeHolder:
            register(cls, fun=func)
        wrapper._pipda_functype = "dispatchable"
    else:
        wrapper._pipda_functype = "func"

    wrapper.registry = MappingProxyType(registry)
    wrapper.dispatch = dispatch
    wrapper.register = register
    wrapper.favorables = MappingProxyType(favorables)

    update_wrapper(wrapper, func)
    update_user_wrapper(
        wrapper,
        name=name,
        qualname=qualname,
        doc=doc,
        module=module,
    )
    return wrapper
