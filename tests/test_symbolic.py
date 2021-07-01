from pipda.context import ContextEval, ContextMixed, ContextSelect
import pytest
from pipda.symbolic import Reference
from pipda import *

from . import f

def test_symbolic(f):
    assert isinstance(f.a, Reference)
    assert isinstance(f['a'], Reference)
    assert f._pipda_eval(1) == 1
    assert f.__index__() is None

def test_reference(f):
    assert f.a._pipda_eval(1, ContextSelect()) == 'a'
    assert repr(f.a) == "DirectRefAttr(parent=<Symbolic:g>, ref='a')"

    with pytest.raises(NotImplementedError):
        f.a._pipda_eval(1, ContextMixed())
    with pytest.raises(NotImplementedError):
        f['a']._pipda_eval(1, ContextMixed())

    assert f['a']._pipda_eval(1, ContextSelect()) == 'a'
    assert f['a']._pipda_eval({'a': 2}, ContextEval()) == 2
    # assert isinstance(f.a.evaluate(1, None), Reference)

    obj = lambda: 0
    obj.a = obj
    obj.b = 2
    assert f.a.b._pipda_eval(obj, ContextEval()) == 2
    # keywords
    obj.ref = 3
    obj.parent = 4
    assert f.ref._pipda_eval(obj, ContextEval()) == 3
    assert f.parent._pipda_eval(obj, ContextEval()) == 4



    data = {'a': {'a': 2}}
    assert f['a']['a']._pipda_eval(data, ContextEval()) == 2

    # with pytest.raises(TypeError):
    assert f[1]._pipda_eval(0, ContextSelect()) == 1

def test_attr_of_directattr(f):
    class Series:
        def __init__(self, elems):
            self.elems = elems

        def split(self, sep=','):
            return [elem.split(sep) for elem in self.elems]

        @property
        def length(self):
            return [len(elem) for elem in self.elems]

    class DF(dict):
        ...

    @register_verb(DF, context=Context.EVAL)
    def mutate(data, **kwargs):
        data = data.copy()
        for key, val in kwargs.items():
            data[key] = val
        return data

    df = DF({'a': Series(['a.b', 'c.de'])})
    out = df >> mutate(b=f['a'].split('.'), c=f['a'].length)
    assert out['b'] == [['a','b'], ['c', 'de']]
    assert out['c'] == [3,4]

