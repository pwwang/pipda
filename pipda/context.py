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
from pipda.utils import evaluate_expr

class ContextBase(ABC): # pragma: no cover

    @abstractmethod
    def getattr(self, data, ref):
        ...

    @abstractmethod
    def getitem(self, data, ref):
        ...

    @property
    def args(self):
        return self

    @property
    def kwargs(self):
        return self

    def __getitem__(self, name: str):
        return getattr(self.__class__, name)

class ContextSelect(ContextBase):

    def getattr(self, data, ref):
        return ref

    def getitem(self, data, ref):
        return evaluate_expr(ref, data, self)

class ContextEval(ContextBase):

    def getattr(self, data, ref):
        return getattr(data, ref)

    def getitem(self, data, ref):
        ref = evaluate_expr(ref, data, self)
        return data[ref]

class ContextMixed(ContextBase):

    def getattr(self, data, ref):
        raise NotImplementedError

    @staticmethod
    def getitem(self, data, ref):
        raise NotImplementedError

    @property
    def args(self):
        return ContextSelect()

    @property
    def kwargs(self):
        return ContextEval()

class Context(Enum):
    """Context to solve f.A and f['A']"""
    UNSET = None
    SELECT = ContextSelect()
    EVAL = ContextEval()
    MIXED = ContextMixed()
