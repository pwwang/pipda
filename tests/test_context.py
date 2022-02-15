import pytest

from pipda.context import *
from pipda import evaluate_expr, Symbolic

def test_context_select():
    cs = ContextSelect()
    assert cs.getattr(None, 'a', 1) == 'a'
    assert cs.getitem(None, 1, 1) == 1

def test_context_eval():
    ce = ContextEval()
    l = []
    assert ce.getattr(l, '__len__', 1) == l.__len__
    assert ce.getitem([1 ,2], 0, 1) == 1

def test_user_context():
    class MyContext(ContextEval):
        def eval_symbolic(self, data):
            return data * 2

    ce = MyContext()
    f = Symbolic()
    out = evaluate_expr(f.__len__(), [1, 2], ce)
    assert out == 4


def test_context_pending():
    cp = ContextPending()
    with pytest.raises(NotImplementedError):
        cp.getattr(None, 'a', 1)
    with pytest.raises(NotImplementedError):
        cp.getitem(None, 'a', 1)

def test_context_mixed():
    cm = ContextMixed()
    with pytest.raises(NotImplementedError):
        cm.getattr(None, 'a', 1)
    with pytest.raises(NotImplementedError):
        cm.getitem(None, 'a', 1)
    assert isinstance(cm.args, ContextSelect)
    assert isinstance(cm.kwargs, ContextEval)

def test_context():
    assert isinstance(Context.PENDING.value, ContextPending)
    assert isinstance(Context.SELECT.value, ContextSelect)
    assert isinstance(Context.EVAL.value, ContextEval)
    assert isinstance(Context.MIXED.value, ContextMixed)
    assert Context.UNSET.value is None
