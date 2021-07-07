import pytest

from pipda.register import *
from pipda.context import Context

from . import identity, iden, iden2, subscribe, iden_func

def test_register_piping():
    with pytest.raises(ValueError):
        register_piping('.')

    register_piping('|')
    assert Verb.CURRENT_SIGN == '|'

    register_piping('>>')

def test_register_verb(identity):

    verb1 = register_verb()(identity)
    assert verb1.__pipda__ == 'Verb'

    with pytest.raises(ValueError):
        register_verb(None)(identity)

    verb2 = register_verb(a=1)(identity)
    assert verb2.__origfunc__.a == 1

def test_register_func(identity):
    func1 = register_func(identity, context=Context.EVAL)
    assert func1.__pipda__ == 'Function'

    func2 = register_func(a=1)(identity)
    assert func2.__origfunc__.a == 1

    ndfunc = register_func(None)(identity)
    assert ndfunc.__pipda__ == 'PlainFunction'

def test_unregister(identity):
    func = register_func()(identity)
    out = unregister(func)
    assert out is identity

    with pytest.raises(ValueError):
        unregister(identity)

def test_not_implemented(identity):
    func = register_func(int)(identity)

    with pytest.raises(NotImplementedError):
        func('a')

def test_verb_calling(iden, iden2):
    out = iden(1)
    assert out == 1

    out = 1 >> iden()
    assert out == 1

    out = 1 >> iden2(iden(2))
    assert out == (1, 2)

def test_dfunc_calling(subscribe, iden2):
    out = [1, 2] >> iden2(subscribe(0))
    assert out == ([1, 2], 1)

def test_ndfunc_calling(iden_func, iden2):
    out = 1 >> iden2(iden_func(2))
    assert out == (1, 2)

    out = iden_func(2)
    assert out == 2

def test_singledispatch_register(subscribe, iden2):
    @subscribe.register(str)
    def _(data, arg):
        return data[arg]

    out = "abcd" >> iden2(subscribe(0))
    assert out == ("abcd", "a")
