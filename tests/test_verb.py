from pipda.context import ContextEval
import pytest
from pipda import *
from pipda.verb import *

def test_verb():
    @register_verb
    def verb(data, x):
        return data[x]

    ret = verb([1], 0)
    assert ret == 1

    ret = [2] >> verb(0)
    assert ret == 2

def test_evaluated():
    v = Verb(round, ContextEval(), (1, ), {})
    assert v.args == (1, )
    assert v.kwargs == {}
    assert v.evaluate(1.123) == 1.1

def test_register_piping_sign():
    assert Verb.CURRENT_SIGN == '>>'

    register_piping_sign('<<')
    assert Verb.CURRENT_SIGN == '<<'
    assert Verb.__rrshift__

    register_piping_sign('>>')

def test_register_piping_sign_inexisting_method():
    with pytest.raises(ValueError):
        register_piping_sign('nosuch')


def test_only_type():
    @register_verb(int)
    def verb(data, x):
        return data + x

    ret = 1 >> verb(2)
    assert ret == 3

    with pytest.raises(NotImplementedError):
        '1' >> verb('2')

    @verb.register(str)
    def _(data, x):
        return data + x + '0'

    ret = '1' >> verb('2')
    assert ret == '120'

def test_context_unset():

    class MyContext(ContextEval):

        def __init__(self):
            self.used = []

        def getitem(self, data, ref):
            self.used.append(ref)
            return super().getitem(data, ref)

        def getattr(self, data, ref):
            self.used.append(ref)
            return super().getattr(data, ref)

    @register_verb(context=Context.UNSET)
    def verb(data, x):
        mycontext = MyContext()

        x = evaluate_expr(x, data, context=mycontext)
        return x, mycontext.used

    f = Symbolic()
    d = {'a': 1, 'b': 2}
    ret, used_refs = d >> verb(f['a'])
    assert ret == 1
    assert used_refs == ['a']

def test_node_na():
    @register_verb
    def verb(data, x):
        return data + x

    with pytest.warns(UserWarning):
        # ast being modified
        assert verb(1, 1) == 2
