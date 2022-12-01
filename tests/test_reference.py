import pytest

from pipda import *
from pipda.context import ContextError, ContextEval


def test_level():
    f = Symbolic()
    assert f.a.b._pipda_level == 2


def test_cant_eval_without_context():
    f = Symbolic()
    with pytest.raises(ContextError):
        f.a._pipda_eval(1)


def test_str():
    f = Symbolic()
    assert str(f.a) == "a"
    assert str(f.a.b) == "a.b"
    assert str(f.a["b"]) == "a[b]"
    assert str(f["a"].b) == "a.b"
    assert str(f[1:3]) == "[1:3]"
    assert str(f[1 : f.b]) == "[1:b]"


def test_attr_eval():
    f = Symbolic()
    data = lambda: 0
    data.x = 10

    out = f.x._pipda_eval(data, Context.EVAL)
    assert out == 10 and isinstance(out, int)


def test_item_eval():
    f = Symbolic()

    out = f["x"]._pipda_eval({"x": 10}, Context.EVAL)
    assert out == 10 and isinstance(out, int)

    # f[...] can also have expression inside
    class ContextTest(ContextEval):
        @property
        def ref(self):
            return Context.SELECT.value

    out = f[f[0]]._pipda_eval([2, 1, 3], ContextTest())
    assert out == 2 and isinstance(out, int)

    out = f[f[0]]._pipda_eval([2, 1, 3], Context.EVAL)
    assert out == 3 and isinstance(out, int)
