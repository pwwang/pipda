import pytest

from pipda.context import *

def test_context_select():
    cs = ContextSelect()
    assert cs.name == 'select'
    assert cs.getattr(None, 'a') == 'a'
    assert cs.getitem(None, 1) == 1

def test_context_eval():
    ce = ContextEval()
    l = []
    assert ce.name == 'eval'
    assert ce.getattr(l, '__len__') == l.__len__
    assert ce.getitem([1 ,2], 0) == 1

def test_context_pending():
    cp = ContextPending()
    assert cp.name == 'pending'
    with pytest.raises(NotImplementedError):
        cp.getattr(None, 'a')
    with pytest.raises(NotImplementedError):
        cp.getitem(None, 'a')

def test_context_mixed():
    cm = ContextMixed()
    assert cm.name == 'mixed'
    with pytest.raises(NotImplementedError):
        cm.getattr(None, 'a')
    with pytest.raises(NotImplementedError):
        cm.getitem(None, 'a')
    assert isinstance(cm.args, ContextSelect)
    assert isinstance(cm.kwargs, ContextEval)

def test_context():
    assert isinstance(Context.PENDING.value, ContextPending)
    assert isinstance(Context.SELECT.value, ContextSelect)
    assert isinstance(Context.EVAL.value, ContextEval)
    assert isinstance(Context.MIXED.value, ContextMixed)
    assert Context.UNSET.value is None
