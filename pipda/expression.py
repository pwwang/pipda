"""Provides the abstract class Expression"""

from abc import ABC, abstractmethod
from functools import partialmethod
from typing import Any

from .context import ContextBase


class Expression(ABC):
    """The abstract Expression class"""

    def __hash__(self) -> int:
        """Make it hashable"""
        return hash(id(self))

    def __getattr__(self, name: str) -> "Expression":
        """Whenever `expr.attr` is encountered,
        return a ReferenceAttr object"""
        # for dispatch
        from .symbolic import ReferenceAttr

        return ReferenceAttr(self, name)

    def __getitem__(self, item: Any) -> "Expression":
        """Whenever `expr[item]` is encountered,
        return a ReferenceAttr object"""
        from .symbolic import ReferenceItem

        return ReferenceItem(self, item)

    def _op_handler(self, op: str, *args: Any, **kwargs: Any) -> "Expression":
        """Handle the operators"""
        from .operator import Operator

        return Operator.REGISTERED(op, (self, *args), kwargs)

    # Make sure the operators connect all expressions into one
    __add__ = partialmethod(_op_handler, "add")
    __radd__ = partialmethod(_op_handler, "radd")
    __sub__ = partialmethod(_op_handler, "sub")
    __rsub__ = partialmethod(_op_handler, "rsub")
    __mul__ = partialmethod(_op_handler, "mul")
    __rmul__ = partialmethod(_op_handler, "rmul")
    __matmul__ = partialmethod(_op_handler, "matmul")
    __rmatmul__ = partialmethod(_op_handler, "rmatmul")
    __truediv__ = partialmethod(_op_handler, "truediv")
    __rtruediv__ = partialmethod(_op_handler, "rtruediv")
    __floordiv__ = partialmethod(_op_handler, "floordiv")
    __rfloordiv__ = partialmethod(_op_handler, "rfloordiv")
    __mod__ = partialmethod(_op_handler, "mod")
    __rmod__ = partialmethod(_op_handler, "rmod")
    __lshift__ = partialmethod(_op_handler, "lshift")
    __rlshift__ = partialmethod(_op_handler, "rlshift")
    __rshift__ = partialmethod(_op_handler, "rshift")
    __rrshift__ = partialmethod(_op_handler, "rrshift")
    __and__ = partialmethod(_op_handler, "and_")
    __rand__ = partialmethod(_op_handler, "rand_")
    __xor__ = partialmethod(_op_handler, "xor")
    __rxor__ = partialmethod(_op_handler, "rxor")
    __or__ = partialmethod(_op_handler, "or_")
    __ror__ = partialmethod(_op_handler, "ror_")
    __pow__ = partialmethod(_op_handler, "pow")
    __rpow__ = partialmethod(_op_handler, "rpow")
    # __contains__() is forced into bool
    # __contains__ = partialmethod(_op_handler, 'contains')

    __lt__ = partialmethod(_op_handler, "lt")  # type: ignore
    __le__ = partialmethod(_op_handler, "le")
    __eq__ = partialmethod(_op_handler, "eq")  # type: ignore
    __ne__ = partialmethod(_op_handler, "ne")  # type: ignore
    __gt__ = partialmethod(_op_handler, "gt")
    __ge__ = partialmethod(_op_handler, "ge")
    __neg__ = partialmethod(_op_handler, "neg")
    __pos__ = partialmethod(_op_handler, "pos")
    __invert__ = partialmethod(_op_handler, "invert")

    # pylint: disable=bad-option-value,invalid-index-returned
    def __index__(self):
        """Allow Expression object to work as indexes"""
        return None

    def __iter__(self):
        """Forbiden iterating on Expression objects

        If it is happening, probably wrong usage of functions/verbs
        """
        raise TypeError(
            "Expression object is not iterable.\n"
            "If you are expecting the evaluated results of the object, try "
            "using the piping syntax or writing it in a independent statement, "
            "instead of an argument of a regular function call."
        )

    @abstractmethod
    def _pipda_eval(
        self,
        data: Any,
        context: ContextBase = None,
    ) -> Any:
        """Evaluate the expression using given data"""
