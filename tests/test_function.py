import pytest

from pipda import register_verb
from pipda.function import *
from pipda.context import Context, ContextEval
from pipda.symbolic import Symbolic
from pipda.reference import ReferenceAttr


def test_function():
    f = Symbolic()

    data = {
        "add": lambda x, y: x + y,
        "sub": lambda x, y: x - y
    }

    @register_func(context=Context.EVAL)
    def arithm(op, x, y):
        return op(x, y)

    call = arithm(f["add"], 4, 1)
    assert str(call) == "arithm(add, 4, 1)"
    assert call._pipda_eval(data) == 5

    call = arithm(f["sub"], 4, y=1)
    assert str(call) == "arithm(sub, 4, y=1)"
    assert call._pipda_eval(data) == 3


def test_refitem_as_func():
    f = Symbolic()

    data = {
        "x": 10,
        "add": lambda x, y: x + y,
    }

    @register_func(context=Context.EVAL)
    def ident(x):
        return x

    out = ident(f["add"](f["x"], 1))
    assert str(out) == "ident(add(x, 1))"
    assert out._pipda_eval(data) == 11


def test_empty_args():
    @register_func
    def fun():
        return 10

    out = fun()
    assert out == 10 and isinstance(out, int)


def test_no_expr_args():
    @register_func
    def add(x, y):
        return x + y

    out = add(1, 2)
    assert out == 3 and isinstance(out, int)
