import pytest

from pipda import *
from pipda.operator import *

from . import f, iden2


class MyOperator(Operator):
    def _op_add(self, a, b):
        return a - b

    @Operator.set_context(context=Context.EVAL)
    def _op_mul(self, a, b):
        return a * b

    @Operator.set_context(
        context=Context.EVAL, extra_contexts={"a": Context.SELECT}
    )
    def _op_sub(self, a, b):
        return a * b


@pytest.fixture
def install_operator():
    register_operator(MyOperator)
    yield
    Operator.OPERATOR = Operator


def test_operator(f, iden2):

    d = {"a": 1, "b": 2}
    ret = d >> iden2(f["a"] + f["b"])
    assert ret[1] == 3

    op = f["a"] + f["b"]
    assert isinstance(op, Operator)
    assert str(op) == 'f[a] + f[b]'

    op2 = -f.a
    assert str(op2) == '-f.a'

    op3 = 1 + f.a
    assert str(op3) == '1 + f.a'

    x = op._pipda_eval(d, Context.EVAL.value)  # not affected
    assert x == 3

def test_operator_getattr(f, iden2):
    d = {"a": "1", "b": "2"}
    ret = d >> iden2((f["a"] + f["b"]).__len__())
    assert ret[1] == 2

def test_operator_nosuch():
    with pytest.raises(ValueError):
        Operator("nosuch", None, (1,), {})
    with pytest.raises(ValueError):
        Operator("rnosuch", None, (1,), {})


def test_register_error():
    class A:
        ...

    with pytest.raises(ValueError):
        register_operator(A)


def test_register(f, iden2, install_operator):

    d = {"a": 1, "b": 2}
    ret = d >> iden2(f["a"] // f["b"])
    assert ret[1] == 0

    ret = d >> iden2(2 // f["b"])
    assert ret[1] == 1

    ret = d >> iden2(f["a"] + f["b"])
    assert ret[1] == -1

    ret = d >> iden2(f["a"] * f["b"])
    assert ret[1] == 2

    ret = d >> iden2(f["a"] - f["b"])
    assert ret[1] == "aa"
