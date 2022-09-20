import pytest
from pipda.symbolic import Symbolic

from pipda.context import Context
from pipda.verb import *


def test_str():
    f = Symbolic()
    class F:
        dep = False
        def __str__(self) -> str:
            return "verb"
    verb = F()

    call = VerbCall(verb, f.x)
    assert str(call) == 'verb(., x)'

    call = VerbCall(verb, x=f.x)
    assert str(call) == 'verb(., x=x)'


def test_pending_context():
    f = Symbolic()

    @register_verb(int, context=Context.PENDING)
    def verb(data, x):
        assert isinstance(x, Expression)

    verb(1, f.x)


def test_extra_contexts():
    f = Symbolic()

    @register_verb(
        dict,
        context=Context.EVAL,
        extra_contexts={'col': Context.SELECT},
    )
    def subset(data, subdata, col):
        return subdata[col]

    out = {"x": {"a": 1}} >> subset(f["x"], col=f.a)
    assert out == 1 and isinstance(out, int)

    out = {"x": {"a": 1}} >> subset(f["x"], f.a)
    assert out == 1 and isinstance(out, int)


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

    @register_verb(
        list,
        context=Context.SELECT,
        extra_contexts={'plus': Context.EVAL},
    )
    def select(data, indices, *, plus):
        return [data[i + plus] for i in indices]

    @select.register(tuple)
    def _(data, indices, *, plus):
        return tuple(data[i + plus] for i in indices)

    class MyList(list): ...

    @select.register(
        MyList,
        context=Context.EVAL,
        extra_contexts={"plus": Context.SELECT},
    )
    def _(data, indices, *, plus):
        return select(list(data), indices, plus=plus)

    out = [1, 2, 3, 4] >> select([f[0], f[2]], plus=f[0])
    assert out == [2, 4] and isinstance(out, list)

    out = (1, 2, 3, 4) >> select([f[0], f[2]], plus=f[0])
    assert out == (2, 4) and isinstance(out, tuple)

    out = MyList([1, 2, 3, 4]) >> select([f[0], f[2]], plus=f[0])
    assert out == [2, 4] and isinstance(out, list)


def test_dependent_verb():
    f = Symbolic()

    @register_verb(list, context=Context.EVAL)
    def times(data, n: int):
        return [x * n for x in data]

    @register_verb(list, context=Context.EVAL, dep=True)
    def length(data):
        return len(data)

    @register_verb(list, context=Context.EVAL, dep=False)
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
            f["a"],  # 1 instead 2
        )
    )
    assert out == {"a": 3, "b": 4, "c": 3}

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
        length(1, 2)


def test_register_piping():

    @register_verb(int)
    def incre(x):
        return x + 1

    out = 1 >> incre()
    assert out == 2 and isinstance(out, int)

    register_piping("|")
    with pytest.raises(TypeError):
        1 >> incre()
    out = 1 | incre()
    assert out == 2 and isinstance(out, int)

    register_piping(">>")
    out = 1 >> incre()
    assert out == 2 and isinstance(out, int)

    with pytest.raises(ValueError):
        register_piping("123")


def test_registered():

    @register_verb(int)
    def incre(x):
        return x + 1

    assert incre.registered(int)
    assert not incre.registered(list)

    @register_verb(None)
    def sum(x):
        return 0

    assert not sum.registered(int)


def test_types_none():

    @register_verb(None)
    def sum_(x):
        """Doc for sum"""
        return 0

    @sum_.register(list)
    def _(x):
        return sum(x)

    assert sum_.__doc__ == "Doc for sum"
    assert sum_.__name__ == "sum_"
    assert sum_.registered(list)
    assert not sum_.registered(object)

    assert sum_("1234") == 0
    assert sum_([1, 2, 3]) == 6
