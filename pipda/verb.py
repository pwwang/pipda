import warnings
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, List, Type
from functools import singledispatch, update_wrapper

from .utils import (
    MultiImplementationsWarning,
    TypeHolder,
    evaluate_expr,
    has_expr,
    update_user_wrapper,
    is_piping,
)
from .context import ContextPending, ContextType
from .piping import PipeableCall


class VerbCall(PipeableCall):
    """A verb call

    Args:
        func: The registered verb
        args: and
        kwargs: The arguments for the verb
    """

    def __init__(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._pipda_func = func
        self._pipda_args = args
        self._pipda_kwargs = kwargs
        self._pipda_backend = kwargs.pop("__backend", None)

    def __str__(self) -> str:
        strargs: List[str] = []
        if not getattr(self._pipda_func, "dependent", False):
            strargs.append(".")

        funname = self._pipda_func.__name__
        if self._pipda_args:
            strargs.extend((str(arg) for arg in self._pipda_args))
        if self._pipda_kwargs:
            strargs.extend(
                f"{key}={val}" for key, val in self._pipda_kwargs.items()
            )
        return f"{funname}({', '.join(strargs)})"

    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        func, disp_context = self._pipda_func.dispatch(
            data.__class__,
            self._pipda_backend,
        )
        context = disp_context or context

        if isinstance(context, Enum):
            context = context.value
        if isinstance(context, ContextPending):
            return func(data, *self._pipda_args, **self._pipda_kwargs)

        args = (evaluate_expr(arg, data, context) for arg in self._pipda_args)
        kwargs = {
            key: evaluate_expr(val, data, context)
            for key, val in self._pipda_kwargs.items()
        }
        return func(data, *args, **kwargs)


def register_verb(
    cls: Type = TypeHolder,
    *,
    func: Callable = None,
    context: ContextType = None,
    name: str = None,
    qualname: str = None,
    doc: str = None,
    module: str = None,
    dependent: bool = False,
    ast_fallback: str = "piping_warning",
    ast_depth: int = 0,
) -> Callable:
    """Register a verb

    A verb is a function that takes a data as the first argument, and uses it
    to evaluate the rest of the arguments. So the first argument is required
    for a verb.

    We can have multiple implementations of a verb for different types of data,
    or evan the same type of data with different backends.

    Args:
        cls: The default type to register for _default backend
            if TypeHolder, it is a generic function, and not counted as a
            real implementation.
        func: The function works as a verb.
            If `None` (not provided), this function will return a decorator.
        context: The context to evaluate the arguments
        name: and
        qualname: and
        doc: and
        module: The meta information about the function to overwrite `func`'s
            or when it's not available from `func`
        dependent: Whether the verb is dependent.
            >>> @register_verb(context=Context.EVAL, dependent=True)
            >>> def length(data):
            >>>     return len(data)
            >>> # with dependent=True
            >>> # length()  -> VerbCall, waiting for data to evaluate
            >>> # with dependent=False
            >>> # length()  -> TypeError, argument data is missing
        ast_fallback: What's the supposed way to call the verb when
            AST node detection fails.
            piping - Suppose this verb is called like `data >> verb(...)`
            normal - Suppose this verb is called like `verb(data, ...)`
            piping_warning - Suppose piping call, but show a warning
            normal_warning - Suppose normal call, but show a warning
            raise - Raise an error
        ast_depth: Whether this verb is wrapped by other wrappers, if so,
            the depth should be provided to make the AST node detection

    Returns:
        The registered verb or a decorator to register a verb
    """
    if func is None:
        return lambda fun: register_verb(
            cls,
            func=fun,
            context=context,
            name=name,
            qualname=qualname,
            doc=doc,
            module=module,
            dependent=dependent,
            ast_fallback=ast_fallback,
            ast_depth=ast_depth,
        )

    def _backend_generic(*args, **kwargs):
        raise NotImplementedError("Not implemented by the given backend.")

    registry = {
        "_default": singledispatch(
            func if cls is TypeHolder else _backend_generic
        )
    }
    # # cannot create weak reference to 'numpy.ufunc' object
    # contexts = weakref.WeakKeyDictionary()
    contexts = {}
    contexts[_backend_generic] = context

    def dispatch(cl, backend=None):
        """generic_func.dispatch(cls, backend) -> <function impl>, <context>

        Runs the dispatch algorithm to return the best available implementation
        for the given *cl* registered on *generic_func* of given *backend*.

        if backend is not provided, we will look for the implementation of
        the backends in reverse order.
        """
        if backend is not None:
            try:
                reg = registry[backend]
            except KeyError:
                raise NotImplementedError(f"No such backend `{backend}`.")
            dispatched = reg.dispatch(cl)
            return dispatched, contexts.get(dispatched, context)

        impls = []
        for backend, reg in reversed(registry.items()):
            fun = reg.dispatch(cl)
            if fun is _backend_generic or (
                fun is func and cls is TypeHolder and backend == "_default"
            ):
                continue

            impls.append((backend, fun, contexts.get(fun, context)))

        if not impls:
            return (func if cls is TypeHolder else _backend_generic), context

        if len(impls) > 1:
            warnings.warn(
                f"Multiple implementations found for `{wrapper.__name__}` "
                f"by backends: [{', '.join(impl[0] for impl in impls)}], "
                "register with more specific types, or pass "
                "`__backend=<backend>` to specify the backend.",
                MultiImplementationsWarning,
            )

        return impls[0][1:]

    def register(cl, backend="_default", context=None, fun=None):
        if fun is None:
            return lambda fn: register(
                cl,
                backend=backend,
                context=context,
                fun=fn,
            )

        if backend not in registry:
            registry[backend] = singledispatch(_backend_generic)

        registry[backend].register(cl, fun)
        if context is not None:
            contexts[fun] = context
        return fun

    def wrapper(*args, **kwargs):
        if dependent:
            return VerbCall(wrapper, *args, **kwargs)

        ast_fb = kwargs.pop("__ast_fallback", ast_fallback)
        if is_piping(wrapper.__name__, ast_fb, ast_depth):
            return VerbCall(wrapper, *args, **kwargs)

        if not args:
            raise TypeError(
                f"Missing the first argument for verb `{wrapper.__name__}`."
            )

        data, *args = args
        if has_expr(data):
            from .function import FunctionCall

            return FunctionCall(wrapper, data, *args, **kwargs)

        return VerbCall(wrapper, *args, **kwargs)._pipda_eval(data)

    if cls:
        register(cls, context=context, fun=func)

    wrapper.registry = MappingProxyType(registry)
    wrapper.dispatch = dispatch
    wrapper.register = register
    wrapper._pipda_functype = "verb"
    update_wrapper(wrapper, func)
    update_user_wrapper(
        wrapper,
        name=name,
        qualname=qualname,
        doc=doc,
        module=module,
    )
    return wrapper
