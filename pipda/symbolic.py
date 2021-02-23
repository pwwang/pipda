"""Provides Symbolic and Reference class"""
from abc import ABC, abstractmethod
from typing import Callable, Optional, Any

import varname.helpers

from .utils import Expression
from .context import Context, ContextBase

class Reference(Expression, ABC):
    """The Reference class, used to define how it should be evaluated
    according to the context (i.e. `f.A`/`f['A']`).

    Args:
        ref: The reference to the subset
        access: How the column is accessed (f.A or f['A'])
        context: The context to evaluate. Should be `None`, and use the one
            passed to `evaluate`
    """
    def __init__(self,
                 ref: Any,
                 context: Optional[ContextBase] = None) -> None:
        super().__init__(context)
        self.ref = ref

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(ref={self.ref!r})'

    def __getattr__(self, name: str) -> Any:
        raise NotImplementedError(
            'Get attribute on Reference object is not implemented yet.'
        )

    def __getitem__(self, item: Any) -> Any:
        raise NotImplementedError(
            'Get item on Reference object is not implemented yet.'
        )

    @abstractmethod
    def evaluate(
            self,
            data: Any,
            context: ContextBase # required
    ) -> Any:
        """Evaluate the reference according to the context

        When context is NAME, evaluate it as a string; when it is DATA,
        evaluate it as a subscript. The index will be also evaluated using the
        data and context. Otherwise the self is returned, which will be pending
        evaluation
        """

class ReferenceAttr(Reference):

    def evaluate(self, data: Any, context: Optional[ContextBase]) -> Any:
        if not context:
            return self
        return context.getattr(data, self.ref)

class ReferenceItem(Reference):

    def evaluate(self, data: Any, context: Optional[ContextBase]) -> Any:
        if not context:
            return self
        return context.getitem(data, self.ref)

@varname.helpers.register
class Symbolic(Expression):
    """The symbolic class, works as a proxy to represent the data

    In most cases it is used to construct the Reference objects.
    """
    def __getattr__(self, name: str) -> Any:
        return ReferenceAttr(name)

    def __getitem__(self, item: Any) -> Any:
        return ReferenceItem(item)

    def __repr__(self) -> str:
        return f"<Symbolic:{self.__varname__}>"

    def evaluate(
            self,
            data: Any,
            context: Optional[ContextBase] = None
    ) -> Any:
        return data
