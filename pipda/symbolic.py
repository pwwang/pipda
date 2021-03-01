"""Provides Symbolic and Reference classes"""
from abc import ABC, abstractmethod
from typing import Optional, Any

import varname.helpers
from varname import config as varname_config

from .utils import Expression, evaluate_expr
from .context import ContextBase

varname_config.ignore_stdlib = False

class Reference(Expression, ABC):
    """The Reference class, used to define how it should be evaluated
    according to the context for references, for example, `f.A`, `f['A']` or
    the references of them (i.e. `f.A.B`, `f.A['b']`, etc)

    Args:
        parent: The parent of this reference. For example: `f.A` for `f.A.B`
        ref: The reference. For example: `B` for `f.A.B`
        context: Defaults to `None`, which should not be specified while
            instansiation. Because these types of expressions are independent.
            A context should be passed to `evaluate` to evaluate the expression.
    """
    def __init__(self,
                 parent: Any,
                 ref: Any,
                 context: Optional[ContextBase] = None) -> None:
        super().__init__(context)

        assert context is None, (
            "No context should be passed to initialize "
            f"a {self.__class__.__name__} object."
        )
        self.parent = parent
        self.ref = ref

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'parent={self.parent!r}, ref={self.ref!r})'
        )

    @abstractmethod
    def evaluate(
            self,
            data: Any,
            context: Optional[ContextBase] = None
    ) -> Any:
        """Evaluate the reference according to the context"""
        assert context is not None, (
            f"Cannot evaluate a {self.__class__.__name__} "
            "object without a context."
        )

class ReferenceAttr(Reference):
    """Attribute references, for example: `f.A`, `f.A.B` etc."""

    def evaluate(
            self,
            data: Any,
            context: Optional[ContextBase] = None
    ) -> Any:
        """Evaluate the attribute references"""
        super().evaluate(data, context)
        parent = evaluate_expr(self.parent, data, context)
        return context.getattr(parent, self.ref)

class ReferenceItem(Reference):
    """Subscript references, for example: `f['A']`, `f.A['B']` etc"""

    def evaluate(
            self,
            data: Any,
            context: Optional[ContextBase] = None
    ) -> Any:
        """Evaluate the subscript references"""
        super().evaluate(data, context)
        parent = evaluate_expr(self.parent, data, context)
        ref = evaluate_expr(self.ref, data, context.ref)
        return context.getitem(parent, ref)

class DirectRefAttr(ReferenceAttr):
    """The direct attribute reference, such as `f.A`"""


class DirectRefItem(ReferenceItem):
    """The direct attribute reference, such as `f['A']`"""

@varname.helpers.register
class Symbolic(Expression):
    """The symbolic class, works as a proxy to represent the data

    In most cases it is used to construct the Reference objects.
    """
    def __getattr__(self, name: str) -> Any:
        """Create a DirectRefAttr object"""
        return DirectRefAttr(self, name)

    def __getitem__(self, item: Any) -> Any:
        """Create a DirectRefItem object"""
        return ReferenceItem(self, item)

    def __repr__(self) -> str:
        return f"<Symbolic:{self.__varname__}>"

    def evaluate(
            self,
            data: Any,
            context: Optional[ContextBase] = None
    ) -> Any:
        """When evaluated, this should just return the data directly"""
        return data
