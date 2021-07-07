import pytest

from pipda.expression import Expression
from pipda.symbolic import ReferenceAttr, ReferenceItem

class Expr(Expression):
    def _pipda_eval(self, data, context):
        ...

def test_expression():

    f = Expr()
    # hashable
    d = {f: 1}
    assert isinstance(f.a, ReferenceAttr)
    assert isinstance(f[1], ReferenceItem)
    assert isinstance(f + 1, Expression)
    assert isinstance(1 + f, Expression)
    assert isinstance(f - 1, Expression)
    assert isinstance(1 - f, Expression)
    assert isinstance(f * 1, Expression)
    assert isinstance(1 * f, Expression)
    assert isinstance(f @ 1, Expression)
    assert isinstance(1 @ f, Expression)
    assert isinstance(f / 1, Expression)
    assert isinstance(1 / f, Expression)
    assert isinstance(f // 1, Expression)
    assert isinstance(1 // f, Expression)
    assert isinstance(f % 1, Expression)
    assert isinstance(1 % f, Expression)
    assert isinstance(f << 1, Expression)
    assert isinstance(1 << f, Expression)
    assert isinstance(f >> 1, Expression)
    assert isinstance(1 >> f, Expression)
    assert isinstance(f & 1, Expression)
    assert isinstance(1 & f, Expression)
    assert isinstance(f | 1, Expression)
    assert isinstance(1 | f, Expression)
    assert isinstance(f ^ 1, Expression)
    assert isinstance(1 ^ f, Expression)
    assert isinstance(f ** 1, Expression)
    assert isinstance(1 ** f, Expression)
    assert isinstance(f > 1, Expression)
    assert isinstance(1 > f, Expression)
    assert isinstance(f < 1, Expression)
    assert isinstance(1 < f, Expression)
    assert isinstance(f == 1, Expression)
    assert isinstance(1 == f, Expression)
    assert isinstance(f != 1, Expression)
    assert isinstance(1 != f, Expression)
    assert isinstance(f >= 1, Expression)
    assert isinstance(1 >= f, Expression)
    assert isinstance(f <= 1, Expression)
    assert isinstance(1 <= f, Expression)
    assert isinstance(-f, Expression)
    assert isinstance(+f, Expression)
    assert isinstance(~f, Expression)

    assert f.__index__() is None

    with pytest.raises(TypeError):
        iter(f)
