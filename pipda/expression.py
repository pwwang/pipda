"""Provides the abstract class Expression"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import partialmethod
from typing import TYPE_CHECKING, Any, Callable

from .context import ContextBase

if TYPE_CHECKING:
    from .operator import OperatorCall
    from .function import FunctionCall
    from .reference import ReferenceAttr, ReferenceItem

OPERATORS = {
    # op, right
    "add": ("+", False),
    "radd": ("+", True),
    "sub": ("-", False),
    "rsub": ("-", True),
    "mul": ("*", False),
    "rmul": ("*", True),
    "matmul": ("@", False),
    "rmatmul": ("@", True),
    "truediv": ("/", False),
    "rtruediv": ("/", True),
    "floordiv": ("//", False),
    "rfloordiv": ("//", True),
    "mod": ("%", False),
    "rmod": ("%", True),
    "lshift": ("<<", False),
    "rlshift": ("<<", True),
    "rshift": (">>", False),
    "rrshift": (">>", True),
    "and_": ("&", False),
    "rand_": ("&", True),
    "xor": ("^", False),
    "rxor": ("^", True),
    "or_": ("|", False),
    "ror_": ("|", True),
    "pow": ("**", False),
    "rpow": ("**", True),
    "lt": ("<", False),
    "le": ("<=", False),
    "eq" : ("==", False),
    "ne" : ("!=", False),
    "gt": (">", False),
    "ge": (">=", False),
    "neg": ("-", False),
    "pos": ("+", False),
    "invert": ("~", False),
}


class Expression(ABC):
    """The abstract Expression class"""

    _pipda_operator = None

    def __array_ufunc__(
        self,
        ufunc: Callable,
        method: str,
        *inputs: Any,
        **kwargs: Any,
    ) -> FunctionCall:
        """Allow numpy ufunc to work on Expression objects"""

        from .piping import PIPING_OPS
        from .verb import VerbCall

        if (
            ufunc.__name__ == PIPING_OPS[VerbCall.PIPING][2]
            and isinstance(inputs[1], VerbCall)
            and len(inputs) == 2
            and method == "__call__"
        ):
            # We can't patch numpy.ndarray
            return inputs[1]._pipda_eval(inputs[0])

        from .function import Function, FunctionCall

        if method == "reduce":
            ufunc = ufunc.reduce

        fun = Function(ufunc, None, {})
        return FunctionCall(fun, *inputs, **kwargs)

    def __hash__(self) -> int:
        """Make it hashable"""
        return hash(id(self))

    def __getattr__(self, name: str) -> ReferenceAttr:
        """Whenever `expr.attr` is encountered,
        return a ReferenceAttr object"""
        if name.startswith("_pipda_"):
            # Avoid recursion
            raise AttributeError

        from .reference import ReferenceAttr
        return ReferenceAttr(self, name)

    def __getitem__(self, item: Any) -> ReferenceItem:
        """Whenever `expr[item]` is encountered,
        return a ReferenceAttr object"""
        from .reference import ReferenceItem
        return ReferenceItem(self, item)

    def _op_method(self, op: str, *operands: Any) -> OperatorCall:
        """Handle the operators"""
        from .operator import Operator, OperatorCall
        from .verb import VerbCall
        if Expression._pipda_operator is None:
            Expression._pipda_operator = Operator()

        # Let the verb handle it
        if (
            not OPERATORS[op][1]
            and OPERATORS.get(f"r{op}", [None])[0] == VerbCall.PIPING
            and isinstance(operands[0], VerbCall)
        ):
            return NotImplemented

        op_func = getattr(Expression._pipda_operator, op)
        return OperatorCall(op_func, op, self, *operands)

    # Make sure the operators connect all expressions into one
    __add__ = partialmethod(_op_method, "add")
    __radd__ = partialmethod(_op_method, "radd")
    __sub__ = partialmethod(_op_method, "sub")
    __rsub__ = partialmethod(_op_method, "rsub")
    __mul__ = partialmethod(_op_method, "mul")
    __rmul__ = partialmethod(_op_method, "rmul")
    __matmul__ = partialmethod(_op_method, "matmul")
    __rmatmul__ = partialmethod(_op_method, "rmatmul")
    __truediv__ = partialmethod(_op_method, "truediv")
    __rtruediv__ = partialmethod(_op_method, "rtruediv")
    __floordiv__ = partialmethod(_op_method, "floordiv")
    __rfloordiv__ = partialmethod(_op_method, "rfloordiv")
    __mod__ = partialmethod(_op_method, "mod")
    __rmod__ = partialmethod(_op_method, "rmod")
    __lshift__ = partialmethod(_op_method, "lshift")
    __rlshift__ = partialmethod(_op_method, "rlshift")
    __rshift__ = partialmethod(_op_method, "rshift")
    __rrshift__ = partialmethod(_op_method, "rrshift")
    __and__ = partialmethod(_op_method, "and_")
    __rand__ = partialmethod(_op_method, "rand_")
    __xor__ = partialmethod(_op_method, "xor")
    __rxor__ = partialmethod(_op_method, "rxor")
    __or__ = partialmethod(_op_method, "or_")
    __ror__ = partialmethod(_op_method, "ror_")
    __pow__ = partialmethod(_op_method, "pow")
    __rpow__ = partialmethod(_op_method, "rpow")
    # __contains__() is forced into bool
    # __contains__ = partialmethod(_op_method, 'contains')

    __lt__ = partialmethod(_op_method, "lt")
    __le__ = partialmethod(_op_method, "le")
    __eq__ = partialmethod(_op_method, "eq")  # type: ignore
    __ne__ = partialmethod(_op_method, "ne")  # type: ignore
    __gt__ = partialmethod(_op_method, "gt")
    __ge__ = partialmethod(_op_method, "ge")
    __neg__ = partialmethod(_op_method, "neg")
    __pos__ = partialmethod(_op_method, "pos")
    __invert__ = partialmethod(_op_method, "invert")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        from .function import FunctionCall
        return FunctionCall(self, *args, **kwargs)

    def __index__(self):
        """Allow Expression object to work as index or part of slice"""
        return None

    def __iter__(self):
        """Forbiden iterating on Expression objects

        If it is happening, probably wrong usage of functions/verbs
        """
        raise TypeError(
            "An Expression object is possible to be iterable only after "
            "it's evaluate. Do you forget to evalute it or you call it in an "
            "unregistered function?"
        )

    @abstractmethod
    def __str__(self) -> str:
        """Used for stringify the whole expression"""

    @abstractmethod
    def _pipda_eval(
        self,
        data: Any,
        context: ContextBase = None,
    ) -> Any:
        """Evaluate the expression using given data"""
