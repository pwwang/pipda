from pipda.context import Context, ContextEval, ContextSelect
import pytest

import sys
from executing import Source
from pipda import register_func
from pipda.function import Function
from pipda.utils import *
from pipda.utils import (
    _get_piping_verb_node,
    _is_piping_verb_argument_node,
    _argument_node_of
)
from . import f, iden, iden2, add1, add2, identity, iden_func, subscribe

def test_null():
    assert repr(NULL) == 'NULL'
    with pytest.raises(InaccessibleToNULLException):
        bool(NULL)
    with pytest.raises(InaccessibleToNULLException):
        len(NULL)
    with pytest.raises(InaccessibleToNULLException):
        NULL.x
    with pytest.raises(InaccessibleToNULLException):
        NULL[0]

def test_dataenv():
    d1 = DataEnv(1)
    assert d1.name == DATA_CONTEXTVAR_NAME
    assert d1.data == 1

    assert d1.get() == 1
    d1.set(2)
    assert d1.get() == 2

    d1.delete()
    assert d1.get() is NULL

def test_get_env_data():
    data = get_env_data(sys._getframe(0))
    assert data is NULL

    _ = DataEnv(1)
    data = get_env_data(sys._getframe(0))
    assert data == 1

def test_get_piping_verb_node(iden2):
    def vnode():
        node = Source.executing(sys._getframe(1)).node
        return _get_piping_verb_node(node)

    out = 1 >> iden2(vnode())
    assert isinstance(out[1], ast.Call)

    out = vnode()
    assert out is None

def test_is_piping_verb_argument_node(iden2):
    def v_arg_node(yes=True):
        node = Source.executing(sys._getframe(1)).node
        verb_node = _get_piping_verb_node(node)
        assert _is_piping_verb_argument_node(node, verb_node) is yes

    1 >> iden2(v_arg_node())
    1 >> iden2((lambda: v_arg_node(False))())
    1 >> iden2(arg=v_arg_node())
    1 >> iden2(arg=(lambda: v_arg_node(False))())

    def no_v_arg_node():
        node = Source.executing(sys._getframe(1)).node
        assert not _is_piping_verb_argument_node(node, None)

    1 >> iden2(no_v_arg_node())

def test_argument_node_of(iden):
    def func():
        node = Source.executing(sys._getframe(1)).node
        return _argument_node_of(node)

    out = iden(func())
    assert out.func.id == 'iden'

def test_bind_arguments(add1, add2):
    out = bind_arguments(add1, (2, ), {})
    assert out.arguments == {'a': 2, 'b': 1}

    with pytest.raises(TypeError):
        bind_arguments(add2, (2,), {})

def test_functype(add1, iden, identity, iden_func, subscribe):
    assert functype(add1) == 'verb'
    assert functype(iden) == 'verb'
    assert functype(identity) == 'plain'
    assert functype(iden_func) == 'plain-func'
    assert functype(subscribe) == 'func'

def test_has_expr(f):
    assert has_expr(f)
    assert not has_expr(1)
    assert has_expr(f+1)
    assert has_expr([f])
    assert has_expr(slice(f, f+1))
    assert has_expr({'a': f})

def test_evaluate_expr():
    class FakeExpr:
        def _pipda_eval(self, data, context):
            return str(data)

    assert evaluate_expr(2, 1, Context.EVAL) == 2
    assert evaluate_expr(FakeExpr(), 1, Context.EVAL) == '1'
    assert evaluate_expr([FakeExpr()], 1, Context.EVAL) == ['1']
    assert evaluate_expr(
        slice(FakeExpr(), FakeExpr()),
        1,
        Context.EVAL
    ) == slice('1', '1')
    assert evaluate_expr({'a': FakeExpr()}, 1, Context.EVAL) == {'a': '1'}

def test_calling_env(iden_func, iden2, identity):
    with pytest.warns(UserWarning):
        assert iden_func(1)

    def piping_verb():
        return calling_env('Verb')

    out = 1 >> iden2(piping_verb())
    assert out[1] is CallingEnvs.PIPING

    out = iden2(1, piping_verb())
    assert out[1] is CallingEnvs.PIPING

    out = identity(piping_verb())
    assert out is None

def test_assume_all_piping(f, add2, iden_func):
    with options_context(assume_all_piping=True):
        out = 1 >> add2(2)
    assert out == 3

    out = iden_func(3)
    assert isinstance(out, int)
    assert out == 3


def test_meta_carried_down():
    from pipda.operator import Operator
    context = ContextEval({"a": 1})

    @register_func(None, context=None)
    def get_context(_context=None):
        return _context.meta["a"]

    expr = Function(get_context, (), {}, False)
    out = evaluate_expr(expr + 2, None, context)
    assert out == 3
