import pytest

from pipda._calling import *
from pipda.utils import NULL, options_context
from . import f, identity, add2, iden_func

def test_verb_calling_rule1(identity):
    out = verb_calling_rule1(identity, (1, ), {}, NULL)
    assert isinstance(out, Verb)

def test_verb_calling_rule2(f, identity):
    out = verb_calling_rule2(identity, (1, ), {}, NULL)
    assert out == 1
    out = verb_calling_rule2(identity, (f, ), {}, NULL)
    assert isinstance(out, FastEvalVerb)

def test_verb_calling_rule3(f, identity):
    out = verb_calling_rule3(identity, (1, ), {}, NULL)
    assert out == 1
    out = verb_calling_rule3(identity, (f, ), {}, NULL)
    assert out is f

def test_verb_calling_rule4(identity):
    out = verb_calling_rule4(identity, (), {}, 1)
    assert out == 1

def test_dfunc_calling_rule1(identity):
    out = dfunc_calling_rule1(identity, (1, ), {}, NULL, True)
    assert isinstance(out, Function)

def test_dfunc_calling_rule2(identity):
    out = dfunc_calling_rule2(identity, (1, ), {}, NULL, False)
    assert out == 1

    with pytest.raises(ValueError):
        dfunc_calling_rule2(identity, (1, ), {}, NULL, True)

def test_dfunc_calling_rule3(identity):
    out = dfunc_calling_rule3(identity, (), {}, 1, False)
    assert out == 1

    with pytest.raises(ValueError):
        dfunc_calling_rule3(identity, (1, ), {}, NULL, True)

def test_ndfunc_calling_rule1(f, identity):
    out = ndfunc_calling_rule1(identity, (1, ), {}, NULL, True)
    assert out == 1

    out = ndfunc_calling_rule1(identity, (f.a, ), {}, NULL, True)
    assert isinstance(out, FastEvalFunction)

def test_ndfunc_calling_rule2(identity):
    out = ndfunc_calling_rule2(identity, (1, ), {}, NULL, False)
    assert out == 1

    with pytest.raises(ValueError):
        ndfunc_calling_rule2(identity, (1, ), {}, NULL, True)

def test_ndfunc_calling_rule3(f, identity):
    out = ndfunc_calling_rule3(identity, (f, ), {}, [1,2], False)
    assert out == [1, 2]

    with pytest.raises(ValueError):
        ndfunc_calling_rule3(identity, (f, ), {}, [1,2], True)

def test_regcall_without_source_works(f, add2, iden_func):
    # works with source
    out = add2([1, 2], iden_func(f[:1]))
    assert out == [1, 2, 1]

    source = "out = add2([1, 2], iden_func(f[:1]))"
    with options_context(warn_astnode_failure=False):
        exec(source)
    assert out == [1, 2, 1]

    source = "out = [1, 2] >> add2(iden_func(f[:1]))"
    with options_context(warn_astnode_failure=False, assume_all_piping=True):
        exec(source)
    assert out == [1, 2, 1]
