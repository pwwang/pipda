import pytest

from pipda import register_verb, register_func
from pipda.function import *
from pipda.context import Context, ContextEval
from pipda.symbolic import DirectRefAttr, ReferenceAttr, Symbolic

from . import f, identity, identity2, iden, iden2


def test_function_repr(identity):
    fun = Function(identity, (), {})
    assert (
        repr(fun) == "Function(func=identity.<locals>.<lambda>, dataarg=True)"
    )
    fun = Function(
        ReferenceAttr(DirectRefAttr(Symbolic("f"), "x"), "mean"),
        (),
        {},
        dataarg=False,
    )
    assert (
        repr(fun)
        == "Function(func=ReferenceAttr(parent=DirectRefAttr(parent=<Symbolic:f>, ref='x'), ref='mean'), dataarg=False)"
    )


def test_function_eval(f, identity):
    out = Function(identity, (), {})._pipda_eval(1, context=Context.EVAL.value)
    assert out == 1
    out = Function(f.__len__, (), {}, False)._pipda_eval(
        [1, 2], context=Context.EVAL.value
    )
    assert out == 2


def test_extra_contexts(f, identity2):
    iden2 = register_verb(extra_contexts={"y": Context.SELECT})(identity2)
    out = iden2(1, f[2])
    assert out == (1, 2)

    iden3 = register_verb(extra_contexts={"z": Context.SELECT})(identity2)
    with pytest.raises(KeyError):
        iden3(1, 2)


def test_context_retrieval(f, iden, iden2):
    @register_func(None, context=Context.UNSET)
    def get_context(dat, _context=None):
        return _context

    out = iden2([1, 2], get_context(f[1]))
    assert isinstance(out[1], ContextEval)


def test_eval_with_pending_context(f, iden2):
    @register_func(context=Context.PENDING)
    def iden(data, arg):
        return arg

    out = 1 >> iden2(iden(f[2]))
    assert out == (1, 2)
