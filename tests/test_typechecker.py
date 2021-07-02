import pytest

import types
from pipda._typechecking import *

class MyList(list):
    ...

@pytest.mark.parametrize('value, type_, exp', [
    (1, int, True),
    ((1,2), typing.Tuple, True),
    ((1,2), typing.Tuple[int, int], True),
    ("abc", typing.Tuple[int], False),
    ({"a": 1}, typing.Mapping, True),
    ({"a": 1}, typing.Mapping[str, int], True),
    ({"a": 1}, typing.Mapping[int, int], False),
    (1, typing.Mapping[int, int], False),
    ([1], typing.Iterable, True),
    ([1], typing.Iterable[int], True),
    ([1], typing.Iterable[str], False),
    (1, typing.Iterable[str], False),
    ([1], typing.List, True),
    ({'a': 1}, typing.Dict, True),
    (MyList([1]), MyList, True),
    (int, typing.Type, True),
    (int, typing.Type[int], True),
    (int, typing.Any, True),
    (int, typing.Callable, True),
    ([1, "a"], typing.List[typing.Any], True),
    ([1, "a"], typing.Union, True),
    (1, typing.Union[int, str], True),
    ("a", typing.Union[int, str], True),
])
def test_typechecker(value, type_, exp):
    assert instanceof(value, type_) is exp
