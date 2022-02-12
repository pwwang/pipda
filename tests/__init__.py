from contextlib import contextmanager

import pytest
from pipda import Symbolic, register_verb, register_func, Context, DataEnv

@pytest.fixture
def f():
    """The global symbolic object"""
    return Symbolic('f')

# some verbs
@pytest.fixture
def add1():
    """A verb to add 2 integers"""
    @register_verb(int, context=Context.EVAL)
    def add(a: int, b: int = 1):
        return a + b
    return add

# some verbs
@pytest.fixture
def add2():
    """A verb to add 2 integers"""
    @register_verb(int, context=Context.EVAL)
    def add(a: int, b: int):
        return a + b
    return add

@pytest.fixture
def iden():
    @register_verb(context=Context.SELECT)
    def iden_(data):
        return data
    return iden_

@pytest.fixture
def iden2():
    @register_verb(context=Context.EVAL)
    def iden_(data, arg):
        return data, arg
    return iden_

@pytest.fixture
def subscribe():
    @register_func((list, tuple, dict))
    def subscribe_(data, arg):
        return data[arg]
    return subscribe_

@pytest.fixture
def iden_func():
    @register_func(None)
    def iden(arg):
        return arg
    return iden

@pytest.fixture
def identity():
    """An identity function"""
    fun = lambda x: x
    fun.__name__ = 'identity'
    return fun

@pytest.fixture
def identity2():
    """An identity function"""
    return lambda x, y: (x, y)

@pytest.fixture
def data_context():
    @contextmanager
    def data_context_(data):
        yield DataEnv(data)

    return data_context_

