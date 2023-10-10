import warnings
import pytest

import numpy as np
from pipda.piping import register_piping
from pipda.symbolic import Symbolic
from pipda.context import Context
from pipda.expression import Expression
from pipda.verb import register_verb, VerbCall
from pipda.utils import MultiImplementationsWarning


def test_str():
    f = Symbolic()

    def verb():
        ...

    call = VerbCall(verb, f.x)
    assert str(call) == "verb(., x)"

    call = VerbCall(verb, x=f.x)
    assert str(call) == "verb(., x=x)"


def test_pending_context():
    f = Symbolic()

    @register_verb(int, context=Context.PENDING)
    def verb(data, x):
        assert isinstance(x, Expression)

    verb(1, f.x)


def test_unregistered_types():
    @register_verb(list)
    def length(data):
        return len(data)

    out = [1, 2] >> length()
    assert out == 2 and isinstance(out, int)

    with pytest.raises(NotImplementedError):
        (1, 2) >> length()


def test_register_more_types():
    @register_verb(list)
    def length(data):
        return len(data)

    @length.register(tuple)
    def _(data):
        return len(data) * 10

    out = [1, 2] >> length()
    assert out == 2 and isinstance(out, int)

    out = (1, 2) >> length()
    assert out == 20 and isinstance(out, int)


def test_register_more_types_inherit_context():
    f = Symbolic()

    @register_verb(list, context=Context.SELECT)
    def select(data, indices, *, plus):
        return [data[i + plus] for i in indices]

    @select.register(tuple)
    def _1(data, indices, *, plus):
        return tuple(data[i + plus] for i in indices)

    class MyList(list):
        ...

    @select.register(MyList, context=Context.EVAL)
    def _2(data, indices, *, plus):
        return select(list(data), indices, plus=plus)

    out = [1, 2, 3, 4] >> select([f[0], f[2]], plus=f[0])
    assert out == [1, 3] and isinstance(out, list)

    out = (1, 2, 3, 4) >> select([f[0], f[2]], plus=f[0])
    assert out == (1, 3) and isinstance(out, tuple)

    out = MyList([1, 2, 3, 4]) >> select([f[0], f[2] - 1], plus=f[0])
    assert out == [3, 4] and isinstance(out, list)


def test_numpy_ufunc():

    fun = register_verb(np.ndarray, func=np.sqrt)
    out = fun(np.array([1, 4, 9]))
    assert out == pytest.approx([1, 2, 3])


def test_dependent_verb():
    f = Symbolic()

    @register_verb(list, context=Context.EVAL)
    def times(data, n: int):
        return [x * n for x in data]

    @register_verb(list, context=Context.EVAL, dependent=True)
    def length(data):
        return len(data)

    @register_verb(list, context=Context.EVAL, dependent=False)
    def length2(data):
        return len(data)

    with pytest.raises(TypeError):
        length2()

    out = length()
    assert isinstance(out, VerbCall)

    out = length([1, 2])
    assert isinstance(out, VerbCall)
    out = length2([1, 2])
    assert out == 2 and isinstance(out, int)

    out = [1, 2] >> length()
    assert out == 2 and isinstance(out, int)
    out = [1, 2] >> length2()
    assert out == 2 and isinstance(out, int)

    out = [1, 2, 3] >> times(length())
    assert out == [3, 6, 9] and isinstance(out, list)
    out = [1, 2, 3] >> times(length2(f[:2]))
    assert out == [2, 4, 6] and isinstance(out, list)


def test_as_func():
    f = Symbolic()

    @register_verb(dict, context=Context.EVAL)
    def update(data, subdata):
        data = data.copy()
        data.update(subdata)
        return data

    @register_verb(dict, context=Context.EVAL)
    def plus(data, n):
        return {key: val + n for key, val in data.items()}

    out = {"a": 1, "b": 2, "c": 3} >> update(plus(f, f["a"]))
    assert out == {"a": 2, "b": 3, "c": 4}

    out = {"a": 1, "b": 2, "c": 3} >> update(
        plus(
            {"a": 2, "b": f["c"]},
            f["a"],  # 2, instead 1
        )
    )
    assert out == {"a": 4, "b": 5, "c": 3}

    out = {"a": 1, "b": 2, "c": 3} >> update(
        plus(
            {"a": 2, "b": 3},
            f["a"],  # 2 instead 1
        )
    )
    assert out == {"a": 4, "b": 5, "c": 3}


def test_error():
    @register_verb(list, context=Context.EVAL)
    def length(data):
        return len(data)

    with pytest.raises(TypeError):
        length([1], 2)


def test_types_none():
    @register_verb()
    def sum_(x):
        """Doc for sum"""
        return 0

    @sum_.register(list)
    def _(x):
        return sum(x)

    assert sum_.__doc__ == "Doc for sum"
    assert sum_.__name__ == "sum_"

    assert sum_("1234", __ast_fallback="normal") == 0
    assert sum_([1, 2, 3], __ast_fallback="normal") == 6


def test_meta():
    name = "myfun"
    qualname = "mypackage.myfun"
    doc = "my doc"
    module = "mypackage"

    fun = register_verb(
        object,
        func=lambda a: None,
        name=name,
        qualname=qualname,
        doc=doc,
        module=module,
    )

    assert fun.__name__ == name
    assert fun.__qualname__ == qualname
    assert fun.__doc__ == doc
    assert fun.__module__ == module


def test_nparray_as_data():
    @register_verb(np.ndarray)
    def sum_(data):
        return data.sum()

    s = np.array([1, 2, 3]) >> sum_()
    assert s == 6 and isinstance(s, np.integer)

    register_piping("|")

    s = np.array([1, 2, 3]) | sum_()
    assert s == 6 and isinstance(s, np.integer)

    register_piping(">>")

    @register_verb(np.ndarray)
    def sum2(data, n):
        return data.sum() + n

    s = np.array([1, 2, 3]) >> sum2(1)
    assert s == 7 and isinstance(s, np.integer)


def test_npufunc_as_verb_args():

    f = Symbolic()

    @register_verb(np.ndarray, context=Context.EVAL)
    def add(data, n):
        return data + n

    out = np.array([1, -2, 3]) >> add(np.abs(f[1]))
    out = list(out)
    assert out == [3, 0, 5] and isinstance(out, list)

    out = np.array([2, -2, 3]) >> add(np.mean(f))
    out = list(out)
    assert out == [3, -1, 4] and isinstance(out, list)


def test_multiple_backends():

    @register_verb(int)
    def add(x, y):
        return x + y

    @add.register((int, set), backend="back")
    def _(x, y):
        return x - y

    with pytest.warns(MultiImplementationsWarning):
        assert add(2, 1, __ast_fallback="normal") == 1

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert add(2, 1, __ast_fallback="normal", __backend="back") == 1
        assert add(2, 1, __ast_fallback="normal", __backend="_default") == 3
        assert add({1, 2}, {1}, __ast_fallback="normal") == {2}

    with pytest.raises(NotImplementedError):
        add(2, 1, __ast_fallback="normal", __backend="not_back")


def test_favored():

    @register_verb(int)
    def add(x, y):
        return x + y

    @add.register(int, backend="back", favored=True)
    def _(x, y):
        return x - y

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert add(2, 1, __ast_fallback="normal") == 1


def test_overwrite_doc():

    @register_verb(int)
    def func(data):
        """doc1"""
        return 1

    @func.register(int, backend="back", overwrite_doc=True)
    def _func(data):
        """doc2"""
        return 2

    assert func.__doc__ == "doc2"


def test_expr_as_data():

    f = Symbolic()

    @register_verb(int)
    def identity(data):
        return data

    @register_verb(int)
    def add(x, y):
        return x + y

    out = 1 >> identity() >> add(f)
    assert out == 2 and isinstance(out, int)


def test_kw_context():

    f = Symbolic()

    @register_verb(
        dict,
        context=Context.EVAL,
        kw_context={'rm': Context.SELECT},
    )
    def update(data, subdata, rm):
        data = data.copy()
        data.update(subdata)
        del data[rm]
        return data

    out = {"a": 1, "b": 2, "c": 3} >> update({"b": f["a"]}, rm=f.a)
    assert out == {"b": 1, "c": 3} and isinstance(out, dict)
