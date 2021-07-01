import pytest
from pipda import *
from pipda.operator import *

from . import f

def test_operator(f):

    @register_verb(context=Context.EVAL)
    def verb(data, x):
        return x

    d = {'a': 1, 'b': 2}
    ret = d >> verb(f['a'] + f['b'])
    assert ret == 3

    op = f['a'] + f['b']
    assert isinstance(op, Operator)

    x = op._pipda_eval(d, Context.EVAL.value) # not affected
    assert x == 3

def test_operator_nosuch():
    with pytest.raises(ValueError):
        Operator('nosuch', None, (1, ), {})
    with pytest.raises(ValueError):
        Operator('rnosuch', None, (1, ), {})

def test_register_error():
    class A:
        ...

    with pytest.raises(ValueError):
        register_operator(A)

def test_register(f):
    class A(Operator):
        def add(self, a, b):
            return a - b

        @Operator.set_context(context=Context.EVAL)
        def mul(self, a, b):
            return a * b

        @Operator.set_context(context=Context.EVAL,
                              extra_contexts={'a': Context.SELECT})
        def sub(self, a, b):
            return a * b

    register_operator(A)

    @register_verb(context=Context.EVAL)
    def verb(data, x):
        return x

    d = {'a': 1, 'b': 2}
    ret = d >> verb(f['a'] // f['b'])
    assert ret == 0

    ret = d >> verb(f['a'] + f['b'])
    assert ret == -1

    ret = d >> verb(f['a'] * f['b'])
    assert ret == 2

    ret = d >> verb(f['a'] - f['b'])
    assert ret == 'aa'

