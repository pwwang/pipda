import pytest

from pipda import *
from pipda.context import *

def test_use_pending():
    f = Symbolic()
    with pytest.raises(NotImplementedError):
        f.a.evaluate(None, context=Context.PENDING.value)
    with pytest.raises(NotImplementedError):
        f['a'].evaluate(None, context=Context.PENDING.value)

def test_use_unset():
    @register_func(context=None)
    def add(data, x):
        ...

    with pytest.raises(ContextError):
        add(1, _env='piping').evaluate(1, context=None)

def test_context_passby():
    f = Symbolic()

    @register_verb(context=Context.SELECT)
    def select(data, *columns):
        return columns

    @register_verb(context=Context.EVAL)
    def seldata(data, *columns):
        return columns

    @register_func(context=Context.UNSET)
    def get(data, col):
        return col

    y = {'a':1, 'b':2, 'c':3} >> select(f['a'], get(f['b']))
    assert y == ('a', 'b')

    y = {'a':1, 'b':2, 'c':3} >> seldata(f['a'], get(f['b']))
    assert y == (1, 2)

def test_mixed():
    f = Symbolic()

    @register_verb(context=Context.MIXED)
    def verb(data, *args, **kwargs):
        return args, kwargs

    out_args, out_kwargs = [0,1,2] >> verb(f[1], f[3], x=f[1], y=f[2])
    assert out_args == (1, 3)
    assert out_kwargs == {'x': 1, 'y': 2}
