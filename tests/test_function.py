import pytest

from collections import OrderedDict
import contextvars
from pipda.utils import DATA_CONTEXTVAR_NAME, DataEnv, functype, unregister

from pipda.verb import Verb
from pipda import *
from pipda.function import *

def test_function():

    @register_func()
    def func(data, x):
        return data[x]

    assert repr(func([0], 1, _env='piping')) == (
        "Function(func='test_function.<locals>.func')"
    )

    ret = func([1], 0)
    assert ret == 1

    @register_verb(context=Context.EVAL)
    def verb(data, x):
        return x

    ret = [2] >> verb(func(0))
    assert ret == 2

def test_function_deep():

    @register_func(context=Context.SELECT)
    def func(data, x):
        return {key: data[key] for key in x}

    @register_verb(context=Context.EVAL)
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
    @register_func(context=Context.EVAL)
    def func(data, x):
        return data[x]

    @register_func(None, context=Context.EVAL)
    def func2(x=-1, y=1):
        return x+y

    @register_func
    def func3(data):
        return len(data)

    @register_verb(context=Context.EVAL)
    def verb(data, x):
        return x

    r = [1, 2] >> verb(func(0) + 1)
    assert r == 2

    r = [1, 2] >> verb(func2() + 1)
    assert r == 1

    r = func(1, _env='piping')([0, 1])
    assert r == 1

    r = func([1,2,3], 2)
    assert r == 3

    r = func2(2,3)
    assert r == 5

    r = func3()
    assert isinstance(r, Function)
    r = r("abcd")
    assert r == 4

def test_context():
    @register_func(context=Context.EVAL)
    def func(data, x):
        return data * x

    @register_func(None, context=Context.EVAL)
    def func2(x):
        return x * 10

    @register_verb(context=Context.EVAL)
    def verb(data, x):
        return data + x

    data = DataEnv(2)
    data2 = DataEnv(100, 'other')

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
    @register_func(context=Context.EVAL)
    def func(data, x):
        return data * x

    @register_verb(context=Context.EVAL)
    def verb(data, func):
        return func(data)

    y = 10 >> verb(lambda d: func(d, 11))
    assert y == 110

def test_register_contexts_for_diff_cls():
    f = Symbolic()

    @register_func(list, context=Context.EVAL)
    def func(data, x):
        return data * x

    @func.register((tuple, dict), context=Context.SELECT)
    def _(data, x):
        return data[x]

    @func.register(str, context=Context.EVAL)
    def _(data, x):
        return data + x

    x = func(f[1], _env='piping')([2, 3])
    assert x == [2, 3] * 3

    x = func(f['a'], _env='piping')({'a': 1})
    assert x == 1

    x = func(f[1], _env='piping')((1, 2, 3))
    assert x == 2

    x = func(f[1], _env='piping')('abc')
    assert x == 'abcb'

def test_unregister():
    def orig(data):
        ...

    registered = register_func(orig)

    assert unregister(registered) is orig
    assert functype(registered) == 'func'
    assert functype(orig) == 'plain'

    registered2 = register_func(None)(orig)

    assert unregister(registered2) is orig
    assert functype(registered2) == 'plain-func'

    with pytest.raises(ValueError):
        unregister(orig)

def test_args_kwargs_have_expr():
    f = Symbolic()
    @register_func(None, context=Context.EVAL)
    def func(x):
        return x

    @register_func(None, context=Context.SELECT)
    def func2(x):
        return x

    out = func(f[0], _env=[1])
    assert out == 1

    out = func(f[0])
    assert isinstance(out, Function)

    out = func([f[0]])
    assert isinstance(out, Function)

    out = func(x=f[0])
    assert isinstance(out, Function)

    out = func(x=[f[0]])
    assert isinstance(out, Function)

    out = func(x={0: f[0]})
    assert isinstance(out, Function)

    @register_func(context=Context.EVAL)
    def func2(data, x):
        return x

    out = func2([1, 2], func(f[1]))
    assert out == 2

def test_func_called_in_different_envs():
    f = Symbolic()
    @register_verb(context=Context.EVAL)
    def verb(data, x):
        return x + 1

    @register_func(context=Context.EVAL)
    def func(data, x):
        return x + 2

    @register_func(None, context=Context.EVAL)
    def func_no_data(x):
        return x + 4

    # called with original func
    out = verb(1, 2)
    assert out == 3

    out = func(1, 2)
    assert out == 4

    out = func_no_data(2)
    assert out == 6

    # called with expression
    out = verb([2], f[0])
    assert out == 3

    out = func([2], f[0])
    assert out == 4

    out = func_no_data(f[0], _env=[2])
    assert out == 6

    # func as verb arg
    out = [2] >> verb(func(f[0]))
    assert out == 5

    out = [2] >> verb(func_no_data(f[0]))
    assert out == 7

def test_verb_arg_only():
    f = Symbolic()
    @register_verb(context=Context.EVAL)
    def verb(data, x):
        return x + 1

    @register_func(context=Context.EVAL)
    def func(data, x):
        return x + 2

    @register_func(context=Context.EVAL, verb_arg_only=True)
    def func2(data, x):
        return x + 4

    @register_func(None, context=Context.EVAL, verb_arg_only=True)
    def func3(x):
        return x + 8

    ret = func(1, 2)
    assert ret == 4

    with pytest.raises(ValueError, match="only"):
        func2(1, 2)
    with pytest.raises(ValueError, match="only"):
        func3(2)

    ret = 1 >> verb(func(2))
    assert ret == 5
    ret = 1 >> verb(func2(2))
    assert ret == 7
    ret = 1 >> verb(func3(2))
    assert ret == 11

def test_extra_contexts():
    f = Symbolic()
    @register_func(dict,
                   context=Context.EVAL,
                   extra_contexts={'cols': Context.SELECT})
    def func(data, cols, **values):
        """Remove cols from data and insert values"""
        ret = {key: val for key, val in data.items() if key not in cols}
        ret.update(values)
        return ret

    x = {'a': 1, 'b': 2}
    y = func(x, ['a'], c=f['a'], d=f['b'])
    assert y == {'b':2, 'c':1, 'd': 2}

    y = func(x, ['a'], c=f['a'], d=f['b']*2)
    assert y == {'b':2, 'c':1, 'd': 4}

def test_extra_contexts_error():
    f = Symbolic()
    @register_func(context=Context.EVAL, extra_contexts={'nosucharg': Context.SELECT})
    def func(data, x): ...

    with pytest.raises(KeyError, match='No such argument'):
        func(1, f.a)

def test_extra_contexts_nodata():
    f = Symbolic()
    @register_func(None,
                   context=Context.EVAL,
                   extra_contexts={'cols': Context.SELECT})
    def func(*cols, **values):
        """Remove cols from data and insert values"""
        return cols, values

    x = func(f['a'], f['b'], a=f['a'], b=f['b'], _env={'a':1, 'b':2})
    assert x[0] == ('a', 'b')
    assert x[1] == {'a':1, 'b':2}
