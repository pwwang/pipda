import pytest  # noqa
import inspect

from pipda.function import (
    register_func,
    FunctionCall,
    PipeableFunction,
    PipeableFunctionCall,
)
from pipda.context import Context
from pipda.symbolic import Symbolic
from pipda.piping import register_piping


def test_function():
    f = Symbolic()

    data = {"add": lambda x, y: x + y, "sub": lambda x, y: x - y}

    @register_func
    def arithm(op, x, y):
        return op(x, y)

    with pytest.raises(ValueError):
        arithm.register(int)

    call = arithm(f["add"], 4, 1)
    assert str(call) == "arithm(add, 4, 1)"
    assert call._pipda_eval(data, Context.EVAL) == 5

    call = arithm(f["sub"], 4, y=1)
    assert str(call) == "arithm(sub, 4, y=1)"
    assert call._pipda_eval(data, Context.EVAL) == 3


def test_refitem_as_func():
    f = Symbolic()

    data = {
        "x": 10,
        "add": lambda x, y: x + y,
    }

    @register_func
    def ident(x):
        return x

    out = ident(f["add"](f["x"], 1))
    assert str(out) == "ident(add(x, 1))"
    assert out._pipda_eval(data, Context.EVAL) == 11


def test_empty_args():
    @register_func
    def fun():
        return 10

    out = fun()
    assert out == 10 and isinstance(out, int)

    out = FunctionCall(fun)._pipda_eval({}, Context.EVAL)
    assert out == 10 and isinstance(out, int)


def test_no_expr_args():
    @register_func
    def add(x, y):
        return x + y

    out = add(1, 2)
    assert out == 3 and isinstance(out, int)


# no extra_context supported for function
def test_extra_contexts():
    @register_func()
    def add(x, plus):
        return f"{x} + {plus}"

    f = Symbolic()
    expr = add(f["a"], f["b"])
    assert expr._pipda_eval({"a": 1, "b": 2}, Context.EVAL) == "1 + 2"


def test_meta():
    name = "myfun"
    qualname = "mypackage.myfun"
    doc = "my doc"
    module = "mypackage"
    signature = inspect.signature(lambda x: None)

    fun = register_func(
        lambda a: None,
        name=name,
        qualname=qualname,
        doc=doc,
        module=module,
        signature=signature,
    )

    assert fun.__name__ == name
    assert fun.__qualname__ == qualname
    assert fun.__doc__ == doc
    assert fun.__module__ == module
    assert fun.signature == signature


def test_dispatchable():
    f = Symbolic()

    @register_func(dispatchable={"x", "y"})
    def add(x, y):
        return x + y

    @add.register(int)
    def _(x, y):
        return x * y

    out = add(1, 2)
    assert out == 2 and isinstance(out, int)

    out = add(1.0, 2.0)
    assert out == 3.0 and isinstance(out, float)

    out = add("a", 3)
    assert out == "aaa" and isinstance(out, str)

    out = add("a", f[0])._pipda_eval([4, "b"], Context.EVAL)
    assert out == "aaaa" and isinstance(out, str)

    out = add("a", f[1])._pipda_eval([4, "b"], Context.EVAL)
    assert out == "ab" and isinstance(out, str)


def test_pipeable():
    @register_func(pipeable=True)
    def add(x, y):
        return x + y

    out = 1 >> add(2)
    assert out == 3 and isinstance(out, int)

    out = add(1, 2)
    assert out == 3 and isinstance(out, int)

    out = PipeableFunctionCall(add.func, 2)._pipda_eval(1, Context.EVAL)
    assert out == 3 and isinstance(out, int)


def test_dispatchable_and_pipeable():
    @register_func(dispatchable={"x", "y"}, pipeable=True)
    def add(x, y):
        return x + y

    @add.register(int)
    def _(x, y):
        return x * y

    out = 1 >> add(2)
    assert out == 2 and isinstance(out, int)

    out = add(1, 2)
    assert out == 2 and isinstance(out, int)

    out = add(1.0, 2.0)
    assert out == 3.0 and isinstance(out, float)

    out = 1.0 >> add(2.0)
    assert out == 3.0 and isinstance(out, float)


def test_register_func_funclass():
    class MyFunction(PipeableFunction):
        ...

    @register_func(pipeable={"x", "y"}, funclass=MyFunction)
    def add(x, y):
        return x + y

    out = 1 >> add(2)
    assert out == 3 and isinstance(out, int)
    out = add(1, 2)
    assert out == 3 and isinstance(out, int)

    register_piping("|")

    out = 1 | add(2)
    assert out == 3 and isinstance(out, int)
    out = add(1, 2)
    assert out == 3 and isinstance(out, int)

    register_piping(">>")
