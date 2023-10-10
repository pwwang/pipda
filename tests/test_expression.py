import pytest

import numpy as np
from pipda.context import Context
from pipda.expression import Expression, register_array_ufunc
from pipda.function import FunctionCall
from pipda.reference import ReferenceAttr, ReferenceItem
from pipda.symbolic import Symbolic
from pipda.verb import register_verb
from pipda.operator import OperatorCall


class Expr(Expression):
    def __str__(self) -> str:
        return ""

    def _pipda_eval(self, data, context):
        ...


def test_expression():

    f = Expr()
    # hashable
    d = {f: 1}  # noqa
    assert isinstance(f.a, ReferenceAttr)
    assert isinstance(f[1], ReferenceItem)
    assert isinstance(f + 1, OperatorCall)
    assert isinstance(1 + f, OperatorCall)
    assert isinstance(f - 1, OperatorCall)
    assert isinstance(1 - f, OperatorCall)
    assert isinstance(f * 1, OperatorCall)
    assert isinstance(1 * f, OperatorCall)
    assert isinstance(f @ 1, OperatorCall)
    assert isinstance(1 @ f, OperatorCall)
    assert isinstance(f / 1, OperatorCall)
    assert isinstance(1 / f, OperatorCall)
    assert isinstance(f // 1, OperatorCall)
    assert isinstance(1 // f, OperatorCall)
    assert isinstance(f % 1, OperatorCall)
    assert isinstance(1 % f, OperatorCall)
    assert isinstance(f << 1, OperatorCall)
    assert isinstance(1 << f, OperatorCall)
    assert isinstance(f >> 1, OperatorCall)
    assert isinstance(1 >> f, OperatorCall)
    assert isinstance(f & 1, OperatorCall)
    assert isinstance(1 & f, OperatorCall)
    assert isinstance(f | 1, OperatorCall)
    assert isinstance(1 | f, OperatorCall)
    assert isinstance(f ^ 1, OperatorCall)
    assert isinstance(1 ^ f, OperatorCall)
    assert isinstance(f**1, OperatorCall)
    assert isinstance(1**f, OperatorCall)
    assert isinstance(f > 1, OperatorCall)
    assert isinstance(1 > f, OperatorCall)
    assert isinstance(f < 1, OperatorCall)
    assert isinstance(1 < f, OperatorCall)
    assert isinstance(f == 1, OperatorCall)
    assert isinstance(1 == f, OperatorCall)
    assert isinstance(f != 1, OperatorCall)
    assert isinstance(1 != f, OperatorCall)
    assert isinstance(f >= 1, OperatorCall)
    assert isinstance(1 >= f, OperatorCall)
    assert isinstance(f <= 1, OperatorCall)
    assert isinstance(1 <= f, OperatorCall)
    assert isinstance(-f, OperatorCall)
    assert isinstance(+f, OperatorCall)
    assert isinstance(~f, OperatorCall)
    assert isinstance(f(), FunctionCall)

    assert f.__index__() is None

    with pytest.raises(TypeError):
        iter(f)


def test_op_to_verb():

    f = Symbolic()

    @register_verb(Expression, context=Context.PENDING)
    def stringify(data):
        return str(data)

    a = f.x >> stringify()
    assert a == "x" and isinstance(a, str)
    assert str(f.x) == "x"


def test_test_pipda_attr():

    f = Expr()
    assert not hasattr(f, "_pipda_xyz")


def test_ufunc():
    f = Symbolic()
    x = np.sqrt(f)
    assert isinstance(x, FunctionCall)

    out = x._pipda_eval(4, Context.EVAL)
    assert out == 2

    out = x._pipda_eval([1, 4], Context.EVAL)
    assert isinstance(out, np.ndarray)
    assert out[0] == 1
    assert out[1] == 2

    x = np.multiply.reduce(f)
    assert isinstance(x, FunctionCall)

    out = x._pipda_eval([1, 2, 3], Context.EVAL)
    assert out == 6 and isinstance(out, np.integer)

    x = np.multiply.accumulate(f)
    assert isinstance(x, FunctionCall)

    out = x._pipda_eval([1, 2, 3], Context.EVAL)
    assert isinstance(out, np.ndarray)
    assert out[0] == 1
    assert out[1] == 2
    assert out[2] == 6

    x = np.multiply.outer(f, f)
    assert isinstance(x, FunctionCall)

    out = x._pipda_eval([1, 2, 3], Context.EVAL)
    assert isinstance(out, np.ndarray)
    assert out[0, 0] == 1
    assert out[0, 1] == 2
    assert out[0, 2] == 3
    assert out[1, 0] == 2
    assert out[1, 1] == 4
    assert out[1, 2] == 6
    assert out[2, 0] == 3
    assert out[2, 1] == 6
    assert out[2, 2] == 9

    x = np.multiply.reduceat(f, [0, 1, 2])
    assert isinstance(x, FunctionCall)

    out = x._pipda_eval([1, 2, 3], Context.EVAL)
    assert isinstance(out, np.ndarray)
    assert out[0] == 1
    assert out[1] == 2
    assert out[2] == 3


def test_register_ufunc():
    old_ufunc = Expression._pipda_array_ufunc

    @register_array_ufunc
    def my_ufunc(ufunc, x, *args, kind, **kwargs):
        return ufunc(x, *args, **kwargs) * 2

    f = Symbolic()
    x = np.sqrt(f)
    assert isinstance(x, FunctionCall)

    out = x._pipda_eval(4, Context.EVAL)
    assert out == 4

    register_array_ufunc(old_ufunc)
