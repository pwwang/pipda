# """Provide helpers to check where a value is a valid type

# https://stackoverflow.com/questions/55503673

# Only support python3.7+, simplified version
# """
# # pylint: disable=unused-argument

# import typing

# def _is_generic(type_):
#     """Check if a type is generic"""
#     if isinstance(type_, typing._GenericAlias):
#         return True

#     if isinstance(type_, typing._SpecialForm):
#         return type_ not in {typing.Any}

#     return False

# def _is_base_generic(type_):
#     """Check if a type is base generic"""
#     if (
#             hasattr(typing, '_SpecialGenericAlias') and
#             isinstance(type_, typing._SpecialGenericAlias)
#     ): # pragma: no cover
#         #python 3.8+
#         return True

#     if isinstance(type_, typing._GenericAlias):
#         protocol = getattr(
#             typing,
#             '_Protocol',
#             getattr(typing, 'Protocol', None)
#         )
#         if type_.__origin__ in {typing.Generic, protocol}:
#             return False # pragma: no cover

#         # if isinstance(type_, typing._VariadicGenericAlias):
#         #     return True

#         return len(type_.__parameters__) > 0

#     if isinstance(type_, typing._SpecialForm):
#         return type_._name in {'ClassVar', 'Union', 'Optional'}

#     return False

# def _is_qualified_generic(type_: typing.Type) -> bool:
#     """Check if a type is a qualified generic"""
#     return (
#         _is_generic(type_) and not _is_base_generic(type_)
#     )

# def _get_base_generic(type_):
#     """Subclasses of Generic will have their _name set to None, but
#     their __origin__ will point to the base generic
#     """
#     if not _is_qualified_generic(type_): # pragma: no cover
#         raise TypeError(
#             f'{type_} is not a qualified Generic and thus has no base'
#         )

#     if type_._name is None:
#         return type_.__origin__

#     return getattr(typing, type_._name)

# def _type_name(type_: typing.Type) -> str:
#     """Get the name of the type"""
#     generic_base = type_
#     if _is_qualified_generic(type_):
#         generic_base = _get_base_generic(type_)

#     return generic_base._name

# ITERABLE_TYPES = {
#     'Container',
#     'Collection',
#     'AbstractSet',
#     'MutableSet',
#     'Sequence',
#     'MutableSequence',
#     'ByteString',
#     'Deque',
#     'List',
#     'Set',
#     'FrozenSet',
#     'KeysView',
#     'ValuesView',
#     'AsyncIterable',
#     'Iterable',
# }

# MAPPING_TYPES = {
#     'Mapping',
#     'MutableMapping',
#     'MappingView',
#     'ItemsView',
#     'Dict',
#     'DefaultDict',
#     'Counter',
#     'ChainMap',
# }

# def _get_subtypes(type_: typing.Type) -> typing.Tuple:
#     """Get the subtypes"""
#     try:
#         return tuple(type_.__args__)
#     except AttributeError:
#         return ()

# def _python_type(type_: typing.Type) -> typing.Type:
#     """Given a type annotation or a class as input,
#     returns the corresponding python class.

#     Examples:
#         >>> _python_type(typing.Dict)
#         <class 'dict'>
#         >>> _python_type(typing.List[int])
#         <class 'list'>
#         >>> _python_type(int)
#         <class 'int'>
#     """
#     try:
#         mro = type_.mro()
#     except AttributeError: # pragma: no cover
#         # if it doesn't have an mro method, it must be a weird typing object
#         return type_.__origin__

#     if typing.Type in mro: # pragma: no cover
#         return type_.python_type
#     if type_.__module__ == 'typing':
#         return type_.__origin__

#     return type_ # pragma: no cover

# def _type_checker(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """General type checker"""
#     if isinstance(value, ignore):
#         return True
#     return isinstance(value, type_)

# def _union_type_checker(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """Type checker for Union"""
#     subtypes = _get_subtypes(type_)
#     if subtypes:
#         return any(instanceof(value, typ, ignore) for typ in subtypes)
#     return True

# def _callable_type_checker(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """Type checker for Callable"""
#     # Ignore the argument types and return types
#     return callable(value)

# def _type_type_checker(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """Type checker for Type"""
#     # Ignore subtypes
#     return isinstance(value, type)

# def _any_type_checker(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """Type checker for Any"""
#     return True

# def _basegeneric_type_checker(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """Type checker for base generic type"""
#     if isinstance(value, ignore):
#         return True
#     return isinstance(value, _python_type(type_))

# def _iterable_type_checker(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """Type checker for iterable types"""
#     if not _basegeneric_type_checker(value, type_, ignore):
#         return False

#     subtype = _get_subtypes(type_)[0]
#     return all(instanceof(val, subtype, ignore) for val in value)

# def _mapping_type_checker(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """Type checker for mapping types"""

#     if not _basegeneric_type_checker(value, type_, ignore):
#         return False

#     keytype, valtype = _get_subtypes(type_)
#     return all(
#         instanceof(key, keytype, ignore) and instanceof(val, valtype, ignore)
#         for key, val in value.items()
#     )

# def _tuple_type_checker(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """Type checker for Tuple"""

#     if not _basegeneric_type_checker(value, type_, ignore):
#         return False

#     subtypes = _get_subtypes(type_)
#     return all(
#         instanceof(val, valtype, ignore)
#         for val, valtype in zip(value, subtypes)
#     )

# def instanceof(
#         value: typing.Any,
#         type_: typing.Type,
#         ignore: typing.Tuple[typing.Type]
# ) -> bool:
#     """Check of a value is of given type"""
#     if type_.__module__ == 'typing':
#         name = _type_name(type_)
#         if name == 'Union':
#             return _union_type_checker(value, type_, ignore)
#         if name == 'Callable':
#             return _callable_type_checker(value, type_, ignore)
#         if name == 'Any':
#             return _any_type_checker(value, type_, ignore)
#         if name == 'Type':
#             return _type_type_checker(value, type_, ignore)

#     if _is_base_generic(type_):
#         return _basegeneric_type_checker(value, type_, ignore)

#     if _is_qualified_generic(type_):
#         name = _type_name(type_)
#         if name in ITERABLE_TYPES:
#             return _iterable_type_checker(value, type_, ignore)

#         if name in MAPPING_TYPES:
#             return _mapping_type_checker(value, type_, ignore)

#         if name == 'Tuple':
#             return _tuple_type_checker(value, type_, ignore)

#     return _type_checker(value, type_, ignore)
