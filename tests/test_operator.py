import pytest

from pipda import *


def test_opcall():

    f = Symbolic()

    op_func = lambda x, y: x + y

    call = OperatorCall(op_func, "invert", 1)
    assert str(call) == "~1"

    call = OperatorCall(op_func, "add", 1, 2)
    assert str(call) == "1 + 2"

    call = OperatorCall(op_func, "radd", 1, f["x"])
    assert str(call) == "x + 1"
    assert call._pipda_eval({"x": 2}, Context.EVAL) == 3


def test_register_operator():

    f = Symbolic()

    @register_operator
    class MyOperator(Operator):
        def add(self, x, y):
            return x * y

        def invert(self, x):
            return -x

    expr = f["x"] + 10
    assert str(expr) == "x + 10"
    assert expr._pipda_eval({"x": 3}, Context.EVAL) == 30

    expr = 10 * f["x"]
    assert str(expr) == "10 * x"
    assert expr._pipda_eval({"x": 2}, Context.EVAL) == 20

    expr = ~f["x"]
    assert str(expr) == "~x"
    assert expr._pipda_eval({"x": 2}, Context.EVAL) == -2

    register_operator(Operator)

    expr = ~f["x"]
    assert str(expr) == "~x"
    assert expr._pipda_eval({"x": 2}, Context.EVAL) == -3  # ~2
