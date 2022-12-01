import pytest  # noqa
import warnings

# from pipda.verb import register_verb
from pipda.function import (
    register_func,
    FunctionCall,
)
from pipda.verb import VerbCall
from pipda.context import Context
from pipda.symbolic import Symbolic
from pipda.utils import MultiImplementationsWarning
# from pipda.piping import register_piping


def test_function():
    f = Symbolic()

    data = {"add": lambda x, y: x + y, "sub": lambda x, y: x - y}

    @register_func
    def arithm(op, x, y):
        return op(x, y)

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
    # signature = inspect.signature(lambda x: None)

    fun = register_func(
        lambda a: None,
        name=name,
        qualname=qualname,
        doc=doc,
        module=module,
        # signature=signature,
    )

    assert fun.__name__ == name
    assert fun.__qualname__ == qualname
    assert fun.__doc__ == doc
    assert fun.__module__ == module
    # assert fun.signature == signature


def test_dispatchable():
    f = Symbolic()

    @register_func(cls=float, dispatchable=True)
    def mul(x, y):
        return x * y

    @mul.register((str, int), backend="back")
    def _(x, y):
        return f"{x} * {y}"

    out = mul(1, 2)
    assert out == "1 * 2" and isinstance(out, str)

    out = mul(1.0, 2.0)
    assert out == 2.0 and isinstance(out, float)

    out = mul("a", 3)
    assert out == "a * 3" and isinstance(out, str)

    out = mul("a", f[0])._pipda_eval([4, "b"], Context.EVAL)
    assert out == "a * 4" and isinstance(out, str)

    out = mul("a", f[1])._pipda_eval([4, "b"], Context.EVAL)
    assert out == "a * b" and isinstance(out, str)

    with pytest.raises(NotImplementedError):
        mul([], [])


def test_dispatchable_noargs():
    @register_func(dispatchable=True)
    def sum_(*args):
        return sum(args)

    @sum_.register(str)
    def _(*args):
        return "".join((str(arg) for arg in args))

    out = sum_(1, 2, 3)
    assert out == 6 and isinstance(out, int)

    out = sum_("1", 2, 3)
    assert out == "123" and isinstance(out, str)

    out = sum_()
    assert out == 0 and isinstance(out, int)


def test_pipeable():
    f = Symbolic()

    @register_func(pipeable=True, context=Context.EVAL)
    def add(x, y):
        return x + y

    out = 1 >> add(2)
    assert out == 3 and isinstance(out, int)

    out = add(1, 2)
    assert out == 3 and isinstance(out, int)

    out = VerbCall(add, 2)._pipda_eval(1, Context.EVAL)
    assert out == 3 and isinstance(out, int)

    out = [1, 2] >> add([f[0]])
    assert out == [1, 2, 1] and isinstance(out, list)


def test_dispatchable_and_pipeable():
    @register_func(dispatchable=True, pipeable=True)
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


def test_backends():

    @register_func(cls=int, dispatchable=True)
    def add(x, y):
        return x + y

    @add.register(int, backend="back")
    def _(x, y):
        return x * y

    with pytest.warns(MultiImplementationsWarning):
        out = add(1, 2)
        assert out == 2 and isinstance(out, int)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        out = add(1, 2, __backend="back")
        assert out == 2 and isinstance(out, int)
        out = add(1, 2, __backend="_default")
        assert out == 3 and isinstance(out, int)

    with pytest.raises(NotImplementedError):
        add(1, 2, __backend="not_exist")

    with pytest.raises(NotImplementedError):
        add(1.0, 2.0, __backend="back")


def test_plain():
    @register_func(plain=True)
    def add0(x, y):
        return x + y

    out = add0(1, 2)
    assert out == 3

    @add0.register(backend="back")
    def _(x, y):
        return x * y

    @register_func(plain=True, cls=object)
    def add(x, y):
        return x + y

    @add.register(backend="back")
    def _(x, y):
        return x * y

    with pytest.warns(MultiImplementationsWarning):
        out = add(1, 2)
        assert out == 2

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        out = add(1, 2, __backend="back")
        assert out == 2
        out = add(1, 2, __backend="_default")
        assert out == 3

    with pytest.raises(NotImplementedError):
        add(1, 2, __backend="back2")

    @register_func(plain=True, cls=object)
    def add2(x, y):
        return x + y

    @add2.register(backend="back", favored=True)
    def _(x, y):
        return x * y

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        out = add2(1, 2)
        assert out == 2


def test_overwrite_doc():

    @register_func(plain=True)
    def func():
        """doc1"""
        return 1

    @func.register(overwrite_doc=True)
    def _func():
        """doc2"""
        return 2

    assert func.__doc__ == "doc2"


def test_pipeable_context():
    f = Symbolic()

    @register_func(pipeable=True, dispatchable=True)
    def func(x):
        ...

    @func.register(list, context=Context.EVAL)
    def _func(x, y):
        return x[y]

    @func.register(str, context=Context.SELECT)
    def _func_str(x, y):
        return x + y

    out = [1, 2, 3] >> func(f[1])
    assert out == 3 and isinstance(out, int)

    out = "abc" >> func(f.x)
    assert out == "abcx" and isinstance(out, str)


def test_dispatchable_args():

    @register_func(cls=int, dispatchable="args")
    def func(x, y):
        return 1

    @func.register(str)
    def _func(x, y):
        return 2

    out = func("a", 2)
    assert out == 2 and isinstance(out, int)

    out = func(2, "a")
    assert out == 1 and isinstance(out, int)

    with pytest.raises(NotImplementedError):
        func(x="a", y=2)


def test_dispatchable_kwargs():

    @register_func(cls=int, dispatchable="kwargs")
    def func(x, y):
        return 1

    @func.register(str)
    def _func(x, y):
        return 2

    out = func("a", y=2)
    assert out == 1 and isinstance(out, int)

    out = func(2, y="a")
    assert out == 2 and isinstance(out, int)

    with pytest.raises(NotImplementedError):
        func("a", 2)


def test_dispatchable_all():

    @register_func(cls=int, dispatchable="all")
    def func(x, y):
        return 1

    @func.register(str)
    def _func(x, y):
        return 2

    out = func("a", y=2)
    assert out == 2 and isinstance(out, int)

    out = func(2, y="a")
    assert out == 1 and isinstance(out, int)

    out = func("a", 2)
    assert out == 2 and isinstance(out, int)


def test_dispatchable_first():

    @register_func(cls=int, dispatchable="first")
    def func(x, y):
        return 1

    @func.register(str)
    def _func(x, y):
        return 2

    out = func("a", 1)
    assert out == 2 and isinstance(out, int)

    out = func(2, "a")
    assert out == 1 and isinstance(out, int)
