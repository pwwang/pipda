import pytest

from pipda.utils import PipingEnvs
from pipda.function import *
from pipda import register_func, register_verb, Symbolic, Context

from . import f

def test_plain_function(f):
    @register_func(None, context=Context.EVAL)
    def mean(x):
        return float(sum(x)) / float(len(x))

    @register_verb(context=Context.EVAL)
    def mutate(data, **kwds):
        for k, v in kwds.items():
            data[k] = v
        return data

    d = {'a': 1, 'b': 2}

    m = mean([1, 2])
    assert m == 1.5

    r = d >> mutate(c=mean([f['a'], f['b']]))
    assert r == {'a': 1, 'b': 2, 'c': 1.5}

def test_plain_context_unset(f):
    def mean(x):
        return float(sum(x)) / float(len(x))

    # with pytest.raises(ValueError,
    #                    match='Common functions cannot be registered'):
    #     register_func(None, func=mean, context=Context.UNSET)

    mean = register_func(None, context=Context.EVAL, func=mean)

    @register_verb(context=Context.EVAL)
    def mutate(data, **kwds):
        for k, v in kwds.items():
            data[k] = v
        return data

    m = mean([1, 2])
    assert m == 1.5
    m = mean([1, 2], _env=PipingEnvs.PIPING)._pipda_eval([1, 2])
    assert m == 1.5

    d = {'a': 1, 'b': 2}
    r = d >> mutate(c=mean([f['a'], f['b']]))
    assert r == {'a': 1, 'b': 2, 'c': 1.5}
