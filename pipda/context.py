"""Provides the context to evaluate f.A and f['A']

By default,
1. in the context of select, both f.A and f['A'] return 'A'
2. in the context of evaluation, f.A returns data.A and f['A'] returns data['A']
3. when it is pending, you will need to evaluate args and kwargs yourself.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Union


class ContextError(Exception):
    """Any errors related to contexts"""


class ContextBase(ABC):
    """The context abstract class, defining how
    the Reference objects are evaluated

    - `getattr` defines how `f.A` is evaluated. Note that `f.A.B` will always
        be evaluated as `getattr(f.A, 'B')`
    - `getitem` defines how `f[item]` is evaluated. Note that the `item` here
        is an evaluated value defined by `getref`.
    - `ref` here defines how the reference/item in `f.item` is evaluated.
        Since we could do `f[f.A]`.
    """

    @abstractmethod
    def getattr(self, parent: Any, ref: str, level: int) -> Any:
        """Defines how `f.A` is evaluated"""

    @abstractmethod
    def getitem(self, parent: Any, ref: Any, level: int) -> Any:
        """Defines how `f[item]` is evaluated"""

    @property
    def ref(self) -> ContextBase:
        """Defines how `item` in `f[item]` is evaluated.

        This function should return a `ContextBase` object."""
        return self


class ContextSelect(ContextBase):
    """Context used in a select context

    In this kind of context,
    - `f.A` works as a shortcut of `'A'`;
    - `f[ref]` works as a shortcut of `ref`. However, `ref` is needed to be
        evaluated by a context returned by `getref`
    """

    def getattr(self, parent: Any, ref: str, level: int) -> str:
        """Get the `ref` directly, regardless of `data`"""
        return ref

    def getitem(self, parent: Any, ref: Any, level: int) -> Any:
        """Get the `ref` directly, which is already evaluated by `f[ref]`"""
        return ref


class ContextEval(ContextBase):
    """Context used in a data-evaluation context

    In this kind of context, the expression is evaluated as-is. That is,
    `f.A` is evaluated as `f.A` and `f[item]` is evaluated as `f[item]`
    """

    def getattr(self, parent: Any, ref: str, level: int) -> Any:
        """How to evaluate `f.A`"""
        return getattr(parent, ref)

    def getitem(self, parent: Any, ref: Any, level: int) -> Any:
        """How to evaluate `f[item]`"""
        return parent[ref]


class ContextPending(ContextBase):
    """Pending context, don't evaluate the expression,
    awaiting next avaiable context"""

    def getattr(self, parent: Any, ref: str, level: int) -> str:
        """Get the `ref` directly, regardless of `data`"""
        raise ContextError("Pending context cannot be used for evaluation.")

    def getitem(self, parent: Any, ref: Any, level: int) -> Any:
        """Get the `ref` directly, which is already evaluated by `f[ref]`"""
        raise ContextError("Pending context cannot be used for evaluation.")


class Context(Enum):
    """Context to solve f.A and f['A']

    PENDING: Context to leave the arguments to be evaluated inside
        the function
    SELECT: It select-based context
    EVAL: It evaluation-based context
    """
    PENDING = ContextPending()
    SELECT = ContextSelect()
    EVAL = ContextEval()


ContextType = Union[Context, ContextBase]
