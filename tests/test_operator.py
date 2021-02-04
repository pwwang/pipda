import pytest
from pipda import *
from pipda.operator import *

def test_operator():
    f = Symbolic()

    @register_verb
    def verb(data, x):
        return x

    d = {'a': 1, 'b': 2}
    ret = d >> verb(f['a'] + f['b'])
    assert ret == 3

    op = f['a'] + f['b']
    assert isinstance(op, Operator)
    assert op.is_piping()
    x = op.evaluate(d, Context.UNSET) # not affected
    assert x == 3

def test_operator_nosuch():
    with pytest.raises(ValueError):
        Operator('nosuch', (1, ), {})

def test_register_error():
    class A:
        ...

    with pytest.raises(ValueError):
        register_operator(A)

def test_register():
    class A(Operator):
        def add(self, a, b):
            return a - b

    register_operator(A)

    f = Symbolic()

    @register_verb
    def verb(data, x):
        return x

    d = {'a': 1, 'b': 2}
    ret = d >> verb(f['a'] - f['b'])
    assert ret == -1


