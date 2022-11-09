import pytest
from pipda.operator import OperatorCall
from pipda.verb import register_verb
from pipda.piping import (
    register_piping,
    patch_classes,
    unpatch_classes,
    PATCHED_CLASSES,
)


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


def test_patching():
    class Data:
        def __init__(self, x):
            self.x = x

        def __rshift__(self, other):
            return self.x + other

    @register_verb(Data)
    def incre(x):
        return x.x + 1

    assert Data(1) >> 2 == 3
    out = Data(1) >> incre()
    # __rshift__ is not patched
    assert isinstance(out, OperatorCall)

    rshift = Data.__rshift__
    patch_classes(Data)
    assert PATCHED_CLASSES[Data]["__rshift__"] is rshift

    out = Data(1) >> incre()
    assert out == 2 and isinstance(out, int)

    assert Data.__rshift__ is not rshift
    # But original __rshift__ still works
    assert Data(1) >> 2 == 3

    unpatch_classes(Data)
    assert Data.__rshift__ is rshift

    # And the original __rshift__ still works
    assert Data(1) >> 2 == 3
    # back to original
    out = Data(1) >> incre()
    assert isinstance(out, OperatorCall)

    register_piping("|")
    # works without patching class as Data has no __or__
    out = Data(1) | incre()
    assert out == 2 and isinstance(out, int)

    register_piping(">>")
    # Since Data is unregistered
    out = Data(1) >> incre()
    assert isinstance(out, OperatorCall)


def test_patching_pandas():

    import pandas as pd

    @register_verb(pd.DataFrame)
    def incre(x):
        return x + 1

    df = pd.DataFrame({"a": [1, 2, 3]})
    out = df >> incre()
    assert out.equals(pd.DataFrame({"a": [2, 3, 4]}))

    out = df | 1
    assert out.equals(pd.DataFrame({"a": [1, 3, 3]}))

    with pytest.raises(TypeError):
        df | incre()

    register_piping("|")
    out = df | incre()
    assert out.equals(pd.DataFrame({"a": [2, 3, 4]}))
    # Original still works
    out = df | 1
    assert out.equals(pd.DataFrame({"a": [1, 3, 3]}))

    # Restore it for other tests
    register_piping(">>")


def test_imethod():
    @register_verb(int)
    def incre(x):
        return x + 1

    a = 1
    a >>= incre()
    assert a == 2

    register_piping("|")
    a = 1
    a |= incre()
    assert a == 2

    register_piping(">>")


def test_patch_imethod():
    class Data:
        def __init__(self, x):
            self.x = x

        def __irshift__(self, other):
            return self.x * other

    @register_verb(Data)
    def incre(x):
        return x.x + 1

    a = Data(1)
    a >>= incre()
    assert a == 2

    register_piping("|")
    a = Data(1)
    a |= incre()
    assert a == 2

    register_piping(">>")
