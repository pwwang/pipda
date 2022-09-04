"""Provides Symbolic and Reference classes"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from .utils import evaluate_expr
from .context import ContextError, ContextType
from .expression import Expression


class Reference(Expression, ABC):
    """The Reference class, used to define how it should be evaluated
    according to the context for references, for example, `f.A`, `f['A']` or
    the references of them (i.e. `f.A.B`, `f.A['b']`, etc)

    Args:
        parent: The parent of this reference. For example: `f.A` for `f.A.B`
        ref: The reference. For example: `B` for `f.A.B`
    """

    def __init__(self, parent: Any, ref: Any) -> None:
        self._pipda_parent = parent
        self._pipda_ref = ref
        self._pipda_level = getattr(self._pipda_parent, "_pipda_level", 0) + 1

    @abstractmethod
    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        """Evaluate the reference according to the context"""
        if context is None:
            # needs context to be evaluated
            raise ContextError(
                f"Cannot evaluate `{self.__class__.__name__}` "
                "object without a context."
            )


class ReferenceAttr(Reference):
    """Attribute references, for example: `f.A`, `f.A.B` etc."""

    def __str__(self) -> str:
        if self._pipda_level == 1:
            return str(self._pipda_ref)
        return f"{self._pipda_parent}.{self._pipda_ref}"

    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        """Evaluate the attribute references"""
        if isinstance(context, Enum):
            context = context.value

        # if we don't have a context here, assuming that
        # we are calling `f.a.b(1)`, instead of evaluation
        super()._pipda_eval(data, context)
        parent = evaluate_expr(self._pipda_parent, data, context)

        return context.getattr(  # type: ignore
            parent,
            self._pipda_ref,
            self._pipda_level,
        )


class ReferenceItem(Reference):
    """Subscript references, for example: `f['A']`, `f.A['B']` etc"""

    def __str__(self) -> str:
        # stringify slice
        if isinstance(self._pipda_ref, slice):
            start = self._pipda_ref.start or ""
            stop = self._pipda_ref.stop or ""
            step = self._pipda_ref.step
            step = "" if step is None else f":{self._pipda_ref.step}"
            ref = f"{start}:{stop}{step}"
            if self._pipda_level == 1:
                ref = f"[{ref}]"
        else:
            ref = str(self._pipda_ref)

        if self._pipda_level == 1:
            return ref
        return f"{self._pipda_parent}[{ref}]"

    def _pipda_eval(self, data: Any, context: ContextType = None) -> Any:
        """Evaluate the subscript references"""
        if isinstance(context, Enum):
            context = context.value

        super()._pipda_eval(data, context)
        parent = evaluate_expr(self._pipda_parent, data, context)
        ref = evaluate_expr(self._pipda_ref, data, context.ref)  # type: ignore

        return context.getitem(parent, ref, self._pipda_level)  # type: ignore
