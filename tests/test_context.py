import pytest

from pipda import *
from pipda.context import *
from pipda.utils import PipingEnvs

from . import f

def test_use_pending(f):
    with pytest.raises(NotImplementedError):
        f.a._pipda_eval(None, context=Context.PENDING.value)
    with pytest.raises(NotImplementedError):
        f['a']._pipda_eval(None, context=Context.PENDING.value)

def test_use_unset(f):
    @register_func(context=None)
    def add(data, x):
        ...

    # No need context, can evaluate
    out = add(1, _env=PipingEnvs.PIPING)._pipda_eval(1, context=None)
    assert out is None

    with pytest.raises(ContextError):
        add(f.a, _env=PipingEnvs.PIPING)._pipda_eval(1, context=None)

def test_context_passby(f):

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

def test_mixed(f):

    @register_verb(context=Context.MIXED)
    def verb(data, *args, **kwargs):
        return args, kwargs

    out_args, out_kwargs = [0,1,2] >> verb(f[1], f[3], x=f[1], y=f[2])
    assert out_args == (1, 3)
    assert out_kwargs == {'x': 1, 'y': 2}

def test_verb_context_as_argument():
    @register_verb(context=Context.EVAL)
    def verb(data, x, _context=None):
        return _context

    # context = 1 >> verb(1)
    # assert context.name == 'eval'

    @register_verb(context=Context.SELECT)
    def verb2(data, x, _context=None):
        return _context

    # context = 1 >> verb2(1)
    # assert context.name == 'select'

    # verb as arg
    @register_verb(context=Context.EVAL)
    def passby(data, x):
        return x

    context = 1 >> passby(verb(1, 1))
    assert context.name == 'eval'

    context = 1 >> passby(verb2(1, 1))
    assert context.name == 'select'

def test_func_context_as_argument():
    @register_verb(context=Context.SELECT)
    def verb_select(data, x):
        return x

    @register_verb(context=Context.EVAL)
    def verb_eval(data, x):
        return x

    @register_func(context=Context.EVAL)
    def func_eval(data, x, _context=None):
        return _context

    @register_func(context=Context.SELECT)
    def func_select(data, x, _context=None):
        return _context

    @register_func(context=Context.UNSET)
    def func_unset(data, x, _context=None):
        return _context

    @register_func(None, context=Context.UNSET)
    def func_unset_nodata(x, _context=None):
        return _context

    context = 1 >> verb_select(func_eval(1))
    assert context.name == 'eval'

    context = 1 >> verb_select(func_select(1))
    assert context.name == 'select'

    context = 1 >> verb_eval(func_eval(1))
    assert context.name == 'eval'

    context = 1 >> verb_eval(func_select(1))
    assert context.name == 'select'

    context = 1 >> verb_select(func_unset(1))
    assert context.name == 'select'

    context = 1 >> verb_eval(func_unset(1))
    assert context.name == 'eval'

    context = 1 >> verb_select(func_unset_nodata(1))
    assert context.name == 'select'

    context = 1 >> verb_eval(func_unset_nodata(1))
    assert context.name == 'eval'

def test_debug(f):
    @register_verb(context=Context.EVAL)
    def verb(data, x, y):
        return x, y

    @register_func(context=None)
    def func1(data, x):
        return x

    @register_func(context=Context.SELECT)
    def func2(data, x):
        return x

    ret = [1,2,3] >> verb(func1(f[2]), func2(func1(f[4])))
    assert ret == (3, 4)
