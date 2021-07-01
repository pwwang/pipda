# import pytest

# import types
# from pipda._typechecking import *

# @pytest.mark.parametrize('type_, checker', [
#     (typing.Union, UnionTypeChecker),  #0
#     (typing.Union[int, str], UnionTypeChecker),
#     (typing.Callable, CallableTypeChecker),
#     (typing.Callable[[], bool], CallableTypeChecker),
#     (typing.Any, AnyTypeChecker),
#     (typing.Type, TypeTypeChecker), #5
#     (typing.Type[int], TypeTypeChecker),
#     (typing.Optional, BaseGenericTypeChecker),
#     (typing.Optional[int], UnionTypeChecker),
#     (typing.Iterable, BaseGenericTypeChecker),
#     (typing.Iterable[int], IterableTypeChecker), #10
#     (typing.List, BaseGenericTypeChecker),
#     (types.FunctionType, TypeChecker),
#     (typing.Mapping, BaseGenericTypeChecker),
#     (typing.Mapping[str, int], MappingTypeChecker),
#     (typing.Tuple, BaseGenericTypeChecker), #15
#     (typing.Tuple[str, int], TupleTypeChecker),
#     (int, TypeChecker),
# ])
# def test_distributor(type_, checker):
#     assert isinstance(type_checker(type_), checker)

# class MyList(list):
#     ...

# @pytest.mark.parametrize('value, type_, exp', [
#     ((1,2), typing.Tuple, True),
#     ((1,2), typing.Tuple[int], True),
#     ("abc", typing.Tuple[int], False),
#     ({"a": 1}, typing.Mapping, True),
#     ({"a": 1}, typing.Mapping[str, int], True),
#     ({"a": 1}, typing.Mapping[int, int], False),
#     (1, typing.Mapping[int, int], False),
#     ([1], typing.Iterable, True),
#     ([1], typing.Iterable[int], True),
#     ([1], typing.Iterable[str], False),
#     (1, typing.Iterable[str], False),
#     ([1], typing.List, True),
#     ({'a': 1}, typing.Dict, True),
#     (MyList([1]), MyList, True),
#     (int, typing.Type, True),
#     (int, typing.Type[int], True),
#     (int, typing.Any, True),
#     (int, typing.Callable, True),
#     ([1, "a"], typing.List[typing.Any], True),
#     ([1, "a"], typing.Union, True),
#     (1, typing.Union[int, str], True),
#     ("a", typing.Union[int, str], True),
# ])
# def test_typechecker(value, type_, exp):
#     assert type_checker(type_).is_typeof(value) is exp
