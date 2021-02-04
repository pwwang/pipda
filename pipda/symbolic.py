"""Provides Symbolic and SubsetRef class"""
from typing import Optional, Any

import varname.helpers

from .utils import Context, Expression, evaluate_expr

class SubsetRef(Expression):
    """The SubsetRef class, used to define how it should be evaluated
    according to the context (i.e. `f.A`/`f['A']`).

    Args:
        ref: The reference to the subset
        access: How the column is accessed (f.A or f['A'])
        context: The context to evaluate. Should be `None`, and use the one
            passed to `evaluate`
    """
    def __init__(self,
                 parent: Expression,
                 ref: Any,
                 access: str,
                 context: Context = Context.UNSET) -> None:
        super().__init__(context)
        self.parent = parent
        self.ref = ref
        self.access = access

    def __getattr__(self, name: str) -> Any:
        self.context = Context.DATA
        return SubsetRef(self, name, 'getattr', Context.DATA)

    def __getitem__(self, item: Any) -> Any:
        self.context = Context.DATA
        return SubsetRef(self, item, 'getitem', Context.DATA)

    def evaluate(self, data: Any, context: Context = Context.UNSET) -> Any:
        """Evaluate the reference according to the context

        When context is NAME, evaluate it as a string; when it is DATA,
        evaluate it as a subscript. The index will be also evaluated using the
        data and context. Otherwise the self is returned, which will be pending
        evaluation
        """
        # only DirectSubsetRef should use the coming in context
        if self.context == Context.NAME:
            if not isinstance(self.ref, str):
                raise TypeError(
                    f"Cannot evaluate {self.ref!r} with context {self.context}"
                )
            return self.ref

        if self.context == Context.DATA:
            # anything happens inside the [] should be interpreted as DATA
            parent = evaluate_expr(self.parent, data, Context.DATA)
            ref = evaluate_expr(self.ref, data, Context.DATA)
            return (
                parent[ref] if self.access == 'getitem'
                else getattr(parent, ref)
            )

        return self

class DirectSubsetRef(SubsetRef):
    """The direct subset reference: f.A or f['A']

    This is the only type of Expression object
    """

    def evaluate(self, data: Any, context: Context = Context.UNSET) -> Any:
        """Evaluate the direct SubsetRef, totally depending on the coming in
        context"""
        if self.context == Context.UNSET:
            self.context = context
        return super().evaluate(data, context)

@varname.helpers.register
class Symbolic(Expression):
    """The symbolic class, works as a proxy to represent the data

    In most cases it is used to construct the SubsetRef objects.
    """
    def __getattr__(self, name: str) -> Any:
        return DirectSubsetRef(self, name, 'getattr')

    def __getitem__(self, item: Any) -> Any:
        return DirectSubsetRef(self, item, 'getitem')

    def __repr__(self) -> str:
        return f"<Symbolic:{self.__varname__}>"

    def evaluate(self, data: Any, context: Optional[Context] = None) -> Any:
        return data
