import pytest

from pipda.context import (
    Context,
    ContextSelect,
    ContextEval,
    ContextPending,
    ContextError,
)
from pipda import evaluate_expr, Symbolic


def test_context_select():
    cs = ContextSelect()
    assert cs.getattr(None, "a", 1) == "a"
    assert cs.getitem(None, 1, 1) == 1


def test_context_eval():
    ce = ContextEval()
    lst = []
    assert ce.getattr(lst, "__len__", 1) == lst.__len__
    assert ce.getitem([1, 2], 0, 1) == 1


def test_user_context():
    class MyContext(ContextEval):
        def getitem(self, parent, ref, level):
            return parent[ref] * 2

        def getattr(self, parent, ref, level):
            return level

    ce = MyContext()
    f = Symbolic()
    out = evaluate_expr(f[1], [1, 2], ce)
    assert out == 4 and isinstance(out, int)

    out = evaluate_expr(f.a.b.c, 1, ce)
    assert out == 3 and isinstance(out, int)


def test_context_pending():
    cp = ContextPending()
    with pytest.raises(ContextError):
        cp.getattr(None, "a", 1)
    with pytest.raises(ContextError):
        cp.getitem(None, "a", 1)


def test_context():
    assert isinstance(Context.PENDING.value, ContextPending)
    assert isinstance(Context.SELECT.value, ContextSelect)
    assert isinstance(Context.EVAL.value, ContextEval)
