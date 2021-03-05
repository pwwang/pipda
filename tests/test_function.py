import pytest

from collections import OrderedDict
import contextvars
from pipda.utils import DATA_CONTEXTVAR_NAME, DataContext

from pipda.verb import Verb
from pipda import *
from pipda.function import *

def test_function():

    @register_func()
    def func(data, x):
        return data[x]

    assert repr(func([0], 1, _calling_type='piping')) == (
        "Function(func='test_function.<locals>.func')"
    )

    ret = func([1], 0)
    assert ret == 1

    @register_verb
    def verb(data, x):
        return x

    ret = [2] >> verb(func(0))
    assert ret == 2

def test_function_deep():

    @register_func(context=Context.SELECT)
    def func(data, x):
        return {key: data[key] for key in x}

    @register_verb
    def verb(data, keys):
        return keys

    f = Symbolic()
    d = {'a': 1, 'b': 2, 'c': 3}
    ret = d >> verb(func([f.a, f.b]))
    assert ret == {'a': 1, 'b': 2}

    ret = d >> verb(func((f.a, f.b)))
    assert ret == {'a': 1, 'b': 2}

    ret = d >> verb(func({f.a, f.b}))
    assert ret == {'a': 1, 'b': 2}

    @register_func(context=Context.SELECT)
    def func_dict(data, x):
        return {key: data[key] for key in x.values()}

    ret = d >> verb(func_dict(OrderedDict([('x', f.a), ('y', f.b)])))
    assert ret == {'a': 1, 'b': 2}

    ret = d >> verb(func_dict({'x': f.a, 'y': f.b}))
    assert ret == {'a': 1, 'b': 2}

def test_function_called_in_normal_way():
    @register_func
    def func(data, x):
        return data[x]

    @register_verb
    def verb(data, x):
        return x

    r = [1, 2] >> verb(func(0) + 1)
    assert r == 2

    r = func(1, _calling_type='piping').evaluate([0, 1])
    assert r == 1

def test_context():
    @register_func
    def func(data, x):
        return data * x

    @register_func(None)
    def func2(x):
        return x * 10

    @register_verb
    def verb(data, x):
        return data + x

    ata = DataContext(100, 'other')
    data = DataContext(2)

    y = verb(2)
    assert y == 4

    # func(2) = 3
    y = verb(func(2))
    assert y == 6

    y = verb(func(2)) >> verb(1)
    assert y == 7

    y = verb(func(2)) >> verb(func(2))
    assert y == 18

    y = verb(func2(2))
    assert y == 22

    y = verb(func2(2)) >> verb(1)
    assert y == 23

    y = verb(func2(2)) >> verb(func2(2))
    assert y == 42

    y = func2(2)
    assert y == 20

    y = func(11)
    assert y == 22

    y = str(func(2))
    # when working as an argument, the function is working in piping mode
    assert 'Function' in y

    data.delete()
    with pytest.raises(TypeError, match='missing 1 required'):
        y = verb(2)

def test_in_lambda():
    @register_func
    def func(data, x):
        return data * x

    @register_verb
    def verb(data, func):
        return func(data)

    y = 10 >> verb(lambda d: func(d, 11))
    assert y == 110
