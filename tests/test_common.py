import pytest

from pipda.utils import evaluate_expr
from pipda.common import *
from pipda import register_verb, Symbolic

def test_common_function():
    @register_common()
    def mean(x):
        return float(sum(x)) / float(len(x))

    @register_verb
    def mutate(data, **kwds):
        for k, v in kwds.items():
            data[k] = v
        return data

    d = {'a': 1, 'b': 2}

    m = mean([1, 2])
    assert m == 1.5

    f = Symbolic()

    r = d >> mutate(c=mean([f['a'], f['b']]))
    assert r == {'a': 1, 'b': 2, 'c': 1.5}

def test_common_context_unset():
    def mean(x):
        return float(sum(x)) / float(len(x))

    with pytest.raises(ValueError,
                       match='Common functions cannot be registered'):
        register_common(mean, context=Context.UNSET)

    mean = register_common(mean)

    @register_verb
    def mutate(data, **kwds):
        for k, v in kwds.items():
            data[k] = v
        return data

    m = mean([1, 2])
    assert m == 1.5

    d = {'a': 1, 'b': 2}
    f = Symbolic()
    r = d >> mutate(c=mean([f['a'], f['b']]))
    assert r == {'a': 1, 'b': 2, 'c': 1.5}
