"""Provides the context to evaluate f.A and f['A']

By default,
1. in the context of select, both f.A and f['A'] return 'A'
2. in the context of evaluation, f.A returns data.A and f['A'] returns data['A']
3. when context is mixed, meaning *args is evaluated with select and
   **kwargs is evaluated with evaluation.
4. when it is unset, you will need to evaluate args and kwargs yourself.

"""

from abc import ABC, abstractmethod, abstractproperty
from enum import Enum
from typing import Any, ClassVar, Union

class ContextError(Exception):
    """Any errors related to contexts"""

class ContextBase(ABC): # pragma: no cover
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
    def getattr(self, parent: Any, ref: str) -> Any:
        """Defines how `f.A` is evaluated"""

    @abstractmethod
    def getitem(self, parent: Any, ref: Any) -> Any:
        """Defines how `f[item]` is evaluated"""

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} @ {hex(id(self))}>'

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

    @abstractproperty
    def name(self) -> str:
        """The name of the context"""

class ContextSelect(ContextBase):
    """Context used in a select context

    In this kind of context,
    - `f.A` works as a shortcut of `'A'`;
    - `f[ref]` works as a shortcut of `ref`. However, `ref` is needed to be
        evaluated by a context returned by `getref`
    """
    name: ClassVar[str] = 'select'

    def getattr(self, parent: Any, ref: str) -> str:
        """Get the `ref` directly, regardless of `data`"""
        return ref

    def getitem(self, parent: Any, ref: Any) -> Any:
        """Get the `ref` directly, which is already evaluated by `f[ref]`"""
        return ref

class ContextEval(ContextBase):
    """Context used in a data-evaluation context

    In this kind of context, the expression is evaluated as-is. That is,
    `f.A` is evaluated as `f.A` and `f[item]` is evaluated as `f[item]`
    """
    name: ClassVar[str] = 'eval'

    def getattr(self, parent: Any, ref: str) -> Any:
        """How to evaluate `f.A`"""
        return getattr(parent, ref)

    def getitem(self, parent: Any, ref: Any) -> Any:
        """How to evaluate `f[item]`"""
        return parent[ref]

    ref = ContextSelect()

class ContextPending(ContextBase):
    """Custom context"""
    name: ClassVar[str] = 'pending'

    def getattr(self, parent: Any, ref: str) -> str:
        """Get the `ref` directly, regardless of `data`"""
        raise NotImplementedError(
            'Custom context cannot be used to evaluate.'
        )

    def getitem(self, parent: Any, ref: Any) -> Any:
        """Get the `ref` directly, which is already evaluated by `f[ref]`"""
        raise NotImplementedError(
            'Custom context cannot be used to evaluate.'
        )


class ContextMixed(ContextBase):
    """A mixed context, where the `*args` are evaluated with `ContextSelect`
    and `**args` are evaluated with `ContextEval`."""
    name: ClassVar[str] = 'mixed'

    def getattr(self, parent: Any, ref: str) -> None:
        raise NotImplementedError(
            "Mixed context should be used via `.args` or `.kwargs`"
        )

    def getitem(self, parent: Any, ref: Any) -> None:
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
