import pytest

from pipda.symbolic import *
from pipda.context import Context

def test_reference_attr():
    refattr = ReferenceAttr([1, 2], '__len__')

    assert repr(refattr) == "ReferenceAttr(parent=[1, 2], ref='__len__')"
    assert isinstance(refattr(), Function)
    assert refattr._pipda_eval(None, Context.EVAL.value)() == 2

    with pytest.raises(ContextError):
        refattr._pipda_eval(None)

def test_reference_item():
    refitem = ReferenceItem([1, 2], 0)
    assert refitem._pipda_eval(None, Context.EVAL.value) == 1

def test_symbolic():
    f = Symbolic()
    assert repr(f) == '<Symbolic:f>'
    assert str(f) == ''

    assert isinstance(f.a, ReferenceAttr)
    assert f.a._pipda_level == 1
    assert f.a.b._pipda_level == 2
    assert str(f.a) == 'a'
    assert str(f.a.b) == 'a.b'

    assert isinstance(f['a'], ReferenceItem)
    assert f['a']._pipda_level == 1
    assert f['a'].b._pipda_level == 2
    assert str(f['a']) == "a"
    assert str(f['a'].b) == "a.b"
    assert str(f['a']['b']) == "a[b]"

    assert f._pipda_eval([1, 2], Context.EVAL.value) == [1, 2]
