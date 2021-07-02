from pipda.utils import functype
from pipda.context import ContextEval
import pytest
from pipda import *
from pipda.verb import *

from . import f

def test_verb(f):

    @register_verb(context=Context.SELECT)
    def verb(data, x):
        return data[x]

    ret = verb([1], 0)
    assert ret == 1

    ret = [2] >> verb(0)
    assert ret == 2

    ret = [1,2,3] >> verb(f[:2])
    assert ret == [1,2]

def test_evaluated():
    v = Verb(round, (1, ), {})
    assert v.args == (1, )
    assert v.kwargs == {}
    assert v._pipda_eval(1.123, Context.EVAL.value) == 1.1

def test_register_piping():
    assert Verb.CURRENT_SIGN == '>>'

    register_piping('<<')
    assert Verb.CURRENT_SIGN == '<<'
    assert Verb.__rrshift__

    register_piping('>>')

def test_register_piping_inexisting_method():
    with pytest.raises(ValueError):
        register_piping('nosuch')


def test_only_type():
    @register_verb(int, context=Context.EVAL)
    def verb(data, x):
        return data + x

    ret = 1 >> verb(2)
    assert ret == 3

    with pytest.raises(NotImplementedError):
        '1' >> verb('2')

    @verb.register(str, context=Context.EVAL)
    def _(data, x):
        return data + x + '0'

    ret = '1' >> verb('2')
    assert ret == '120'

def test_context_unset(f):

    class MyContext(ContextEval):

        def __init__(self):
            self.used = []

        def getitem(self, data, ref, is_direct):
            if is_direct:
                self.used.append(ref)
            return super().getitem(data, ref)

        def getattr(self, data, ref, is_direct):
            if is_direct:
                self.used.append(ref)
            return super().getattr(data, ref)

    @register_verb(context=Context.PENDING)
    def verb(data, x):
        mycontext = MyContext()

        x = evaluate_expr(x, data, context=mycontext)
        return x, mycontext.used

    d = {'a': 1, 'b': {'c': 2}}
    ret, used_refs = d >> verb(f['a'])
    assert ret == 1
    assert used_refs == ['a']

    ret, used_refs = d >> verb(f['b']['c'])
    assert ret == 2
    assert used_refs == ['b']

def test_node_na():
    @register_verb(context=Context.EVAL)
    def verb(data, x):
        return data + x

    with pytest.warns(UserWarning):
        # ast being modified
        assert verb(1, 1) == 2

def test_context():
    @register_verb(context=Context.EVAL)
    def verb(data, x):
        return data + x

    data0 = DataEnv(100, 'whatever')
    _ = DataEnv(12)
    y = verb(3)
    assert y == 15

    y = verb(3) >> verb(1)
    assert y == 16

def test_diff_contexts_for_diff_types(f):
    @register_verb(str, context=Context.EVAL)
    def verb(data, x):
        return data + x

    @verb.register(dict, context=Context.SELECT)
    def _(data, x):
        ret = data.copy()
        ret[x] = data[x] * 2
        return ret

    @verb.register((list, tuple), context=Context.EVAL) # eval
    def _(data, x):
        return data + type(data)([x])

    @verb.register(int, context=Context.PENDING)
    def _(data, x):
        return verb([data], x)

    y = 'abc' >> verb(f[1])
    assert y == 'abcb'

    y = {'a': 1} >> verb(f['a'])
    assert y == {'a': 2}

    y = [1,2,3] >> verb(f[1])
    assert y == [1,2,3,2]

    y = [1,2,3] >> verb(f[1])
    assert y == [1,2,3,2]

    y = (1,2,3) >> verb(f[2])
    assert y == (1,2,3,3)

    y = 1 >> verb(f[0])
    assert y == [1, 1]

def test_verb_as_arg(f):
    @register_verb(list, context=Context.EVAL)
    def add(data, x):
        return data + x

    @register_verb(list, context=Context.EVAL)
    def lenof(data):
        return len(data)

    # y = [1,2] >> add([lenof(f)])
    # assert y == [1, 2, 2]

    # y = [1,2] >> add([lenof([lenof(f)])])
    # assert y == [1, 2, 1]

    @register_func(context=Context.EVAL)
    def func(data):
        return len(data)

    y = [1,2] >> add([lenof([func()])])
    assert y == [1, 2, 1]


def test_unregister():
    def orig(data):
        ...

    registered = register_verb(orig)

    assert unregister(registered) is orig
    assert functype(registered) == 'verb'

def test_keyword_attr(f):
    @register_verb(context=Context.EVAL)
    def prod(data, *args):
        ret = 1
        for arg in args:
            ret *= arg
        return ret

    data = lambda: 0
    data.func = 2
    data.datarg = 3
    data.args = 4
    data.kwargs = 5
    data.parent = 6
    data.ref = 7
    data.data = 8
    data.op = 9

    ret = data >> prod(
        f.func, f.datarg, f.args, f.kwargs,
        f.parent, f.ref, f.data, f.op
    )
    assert ret == 362880

def test_astnode_fail_warning():
    # default
    @register_func(context=Context.SELECT)
    def func(data, x):
        return data[x]

    with pytest.warns(UserWarning):
        assert func([1,2], 1) == 2

    register_func.astnode_fail_warning = False
    with pytest.warns(None) as record:
        assert func([1,2], 1) == 2
    assert len(record) == 0
    register_func.astnode_fail_warning = True

def test_inplace_pipe():

    @register_verb(context=Context.SELECT)
    def verb(data, x, y):
        copied = data[:]
        copied[x] = y
        return copied

    x = [1,2,3]
    x >>= verb(1,4)
    assert x == [1,4,3]

def test_register_with_attrs():
    @register_verb(context=Context.PENDING)
    def verb(data, x):
        return x

    @register_verb(object, attr=1)
    def verb1(data):
        return 1

    @register_verb(attr=2)
    def verb2(data):
        return 2

    out = None >> verb(verb1())
    assert out.func.attr == 1

    out = None >> verb(verb2())
    assert out.func.attr == 2

def test_called_regularly(f):
     @register_verb(context=Context.SELECT)
     def select(df, col1, col2):
         return tuple(getattr(df, col) for col in (col1, col2))

     df = lambda: 0
     df.a = 1
     df.b = 2
     df.c = 3

     out = select(df=df, col1=f.a, col2=f.b)
     assert out == (1,2)

     @register_verb(context=Context.EVAL)
     def diag(x = 1, n = None):
         return [x] * n

     @diag.register(list)
     def _(x = 1, n = None):
         return x * n

     out = diag(1, 3)
     assert (out == [1,1,1]) is True
     out = diag([1], 3)
     assert (out == [1,1,1]) is True

def test_called_regularly_with_func(f):
    # GH11
    @register_verb(dict, context=Context.SELECT)
    def select(df, cols):
        return tuple(df[col] for col in cols)

    @register_func
    def where(df, fun):
        return [col for col in df if fun(df[col])]

    @register_func(None)
    def add(xy):
        return [''.join(xy)]

    is_even = lambda x: x % 2 == 0

    df = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'bd': 5}
    out = df >> select(where(is_even))
    assert out == (2, 4)

    out = where(df, is_even)
    assert out == ['b', 'd']

    out = select(df, where(is_even))
    assert out == (2, 4)

    out = select(df, add(where(is_even)))
    assert out == (5, )

    out = where(is_even)
    assert isinstance(out, Function)

def test_error_when_register_none_type():
    with pytest.raises(ValueError):
        register_verb(None, func=lambda x: x)

def test_try_ambiguous_regular_calling(f):
    @register_verb(int, context=Context.SELECT)
    def add(a:int, b:int, c:int=1):
        return a + b + c

    with pytest.warns(UserWarning, match="ambiguity"):
        out = add(2, 3)
    assert out == 6

    with pytest.warns(UserWarning, match="ambiguity"):
        out = add(2, f[3])
    assert out == 6

    # extra value to avoid warning
    out = add(2, 3, 1)
    assert out == 6

    with pytest.raises(TypeError):
        add(2.1, 3.1)

    @register_verb(int)
    def add2(a: int, b:int = 1):
        return a + b

    with pytest.warns(UserWarning, match="ambiguity"):
        out = add2(2)

    assert out == 3
