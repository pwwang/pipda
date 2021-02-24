from pipda.context import ContextEval, ContextMixed, ContextSelect
import pytest
from pipda.symbolic import Reference
from pipda import *

def test_symbolic():
    f = Symbolic()
    assert isinstance(f.a, Reference)
    assert isinstance(f['a'], Reference)
    assert f.evaluate(1) == 1

def test_reference():
    f = Symbolic()
    assert f.a.evaluate(1, ContextSelect()) == 'a'
    assert repr(f.a) == "DirectRefAttr(parent=<Symbolic:f>, ref='a')"

    with pytest.raises(NotImplementedError):
        f.a.evaluate(1, ContextMixed())
    with pytest.raises(NotImplementedError):
        f['a'].evaluate(1, ContextMixed())

    assert f['a'].evaluate(1, ContextSelect()) == 'a'
    assert f['a'].evaluate({'a': 2}, ContextEval()) == 2
    # assert isinstance(f.a.evaluate(1, None), Reference)
    obj = lambda: 0
    obj.a = obj
    obj.b = 2
    assert f.a.b.evaluate(obj, ContextEval()) == 2
    data = {'a': {'a': 2}}
    assert f['a']['a'].evaluate(data, ContextEval()) == 2

    # with pytest.raises(TypeError):
    assert f[1].evaluate(0, ContextSelect()) == 1
