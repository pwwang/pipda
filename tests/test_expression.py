import pytest

from pipda.context import Context
from pipda.expression import Expression
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
    d = {f: 1}
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
    assert isinstance(f ** 1, OperatorCall)
    assert isinstance(1 ** f, OperatorCall)
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
    # assert a == 'x'
    assert str(f.x) == 'x'


def test_test_pipda_attr():

    f = Expr()
    assert not hasattr(f, "_pipda_xyz")
