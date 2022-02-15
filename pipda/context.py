"""Provides the context to evaluate f.A and f['A']

By default,
1. in the context of select, both f.A and f['A'] return 'A'
2. in the context of evaluation, f.A returns data.A and f['A'] returns data['A']
3. when context is mixed, meaning *args is evaluated with select and
   **kwargs is evaluated with evaluation.
4. when it is unset, you will need to evaluate args and kwargs yourself.

"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Mapping, Union


class ContextError(Exception):
    """Any errors related to contexts"""


class ContextBase(ABC):  # pragma: no cover
    """The context abstract class, defining how
    the Reference objects are evaluated

    - `getattr` defines how `f.A` is evaluated. Note that `f.A.B` will always
        be evaluated as `getattr(f.A, 'B')`
    - `getitem` defines how `f[item]` is evaluated. Note that the `item` here
        is an evaluated value defined by `getref`.
    - `ref` here defines how the reference/item in `f.item` is evaluated.
        Since we could do `f[f.A]`.
    """

    def __init__(self, meta: Mapping[str, Any] = None):
        """Meta data is carring down"""
        self.meta = meta or {}

    def eval_symbolic(self, data: Any) -> Any:
        return data

    @abstractmethod
    def getattr(self, parent: Any, ref: str, level: int) -> Any:
        """Defines how `f.A` is evaluated"""

    @abstractmethod
    def getitem(self, parent: Any, ref: Any, level: int) -> Any:
        """Defines how `f[item]` is evaluated"""

    def update_meta_from(self, other_context: "ContextBase") -> None:
        """Update meta data from other context"""
        if other_context is not None:
            self.meta.update(
                {
                    key: mval
                    for key, mval in other_context.meta.items()
                    if key not in self.meta
                }
            )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} @ {hex(id(self))}>"

    @property
    def ref(self) -> "ContextBase":
        """Defines how `item` in `f[item]` is evaluated.

        This function should return a `ContextBase` object."""
        return self

    @property
    def args(self) -> "ContextBase":
        """The context to evaluate `*args` passed to a function"""
        return self

    @property
    def kwargs(self) -> "ContextBase":
        """The context to evaluate `**kwargs` passed to a function"""
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
    """Pending context"""

    def getattr(self, parent: Any, ref: str, level: int) -> str:
        """Get the `ref` directly, regardless of `data`"""
        raise NotImplementedError(
            "Pending context cannot be used to evaluate."
        )

    def getitem(self, parent: Any, ref: Any, level: int) -> Any:
        """Get the `ref` directly, which is already evaluated by `f[ref]`"""
        raise NotImplementedError(
            "Pending context cannot be used to evaluate."
        )


class ContextMixed(ContextBase):
    """A mixed context, where the `*args` are evaluated with `ContextSelect`
    and `**args` are evaluated with `ContextEval`."""

    def getattr(self, parent: Any, ref: str, level: int) -> None:
        raise NotImplementedError(
            "Mixed context should be used via `.args` or `.kwargs`"
        )

    def getitem(self, parent: Any, ref: Any, level: int) -> None:
        raise NotImplementedError(
            "Mixed context should be used via `.args` or `.kwargs`"
        )

    @property
    def args(self):
        return ContextSelect()

    @property
    def kwargs(self):
        return ContextEval()


class Context(Enum):
    """Context to solve f.A and f['A']

    UNSET: The function's evaluation is dependent on it's parents
    PENDING: Context to leave the arguments to be evaluated inside
        the function
    SELECT: It select-based context
    EVAL: It evaluation-based context
    MIXED: Mixed context.
        For *args, used select-based;
        for **kwargs, use evaluation-based.
    """

    UNSET = None
    PENDING = ContextPending()
    SELECT = ContextSelect()
    EVAL = ContextEval()
    MIXED = ContextMixed()


ContextAnnoType = Union[Context, ContextBase]
