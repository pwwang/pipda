# """Provide helpers to check where a value is a valid type

# https://stackoverflow.com/questions/55503673

# Only support python3.7+, simplified version
# """
# import typing

# def is_generic(type_):
#     """Check if a type is generic"""
#     if isinstance(type_, typing._GenericAlias):
#         return True

#     if isinstance(type_, typing._SpecialForm):
#         return type_ not in {typing.Any}

#     return False

# def is_base_generic(type_):
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

# def is_qualified_generic(type_: typing.Type) -> typing.Type:
#     """Check if a type is a qualified generic"""
#     return (
#         is_generic(type_) and not is_base_generic(type_)
#     )

# def get_base_generic(type_):
#     """Subclasses of Generic will have their _name set to None, but
#     their __origin__ will point to the base generic
#     """
#     if not is_qualified_generic(type_): # pragma: no cover
#         raise TypeError(
#             f'{type_} is not a qualified Generic and thus has no base'
#         )

#     if type_._name is None:
#         return type_.__origin__

#     return getattr(typing, type_._name)

# def type_name(type_: typing.Type) -> str:
#     """Get the name of the type"""
#     generic_base = type_
#     if is_qualified_generic(type_):
#         generic_base = get_base_generic(type_)

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



# class TypeChecker:
#     """General type checker"""
#     def __init__(self, type_):
#         self.type_ = type_

#     def is_typeof(self, value: typing.Any) -> bool:
#         """Check if a value is of this type"""
#         return isinstance(value, self.type_)


# class UnionTypeChecker(TypeChecker):
#     """Type checker for Union"""
#     @property
#     def subtypes(self) -> typing.Tuple[TypeChecker]:
#         """Get the subtypes"""
#         try:
#             return tuple(type_checker(arg) for arg in self.type_.__args__)
#         except AttributeError:
#             return ()

#     def is_typeof(self, value: typing.Any) -> bool:
#         """Check if a value is of this type"""
#         subtypes = self.subtypes
#         if subtypes:
#             return any(typ.is_typeof(value) for typ in self.subtypes)
#         return True

# class CallableTypeChecker(TypeChecker):
#     """Type checker for Callable"""

#     def is_typeof(self, value: typing.Any) -> bool:
#         """Check if a value is of this type"""
#         # Ignore the argument types and return types
#         return callable(value)

# class TypeTypeChecker(TypeChecker):
#     """Type checker for Type"""

#     def is_typeof(self, value: typing.Any) -> bool:
#         """Check if a value is of this type"""
#         # Ignore subtypes
#         return isinstance(value, type)

# class AnyTypeChecker(TypeChecker):
#     """Type checker for Any"""

#     def is_typeof(self, value: typing.Any) -> bool:
#         """Check if a value is of this type"""
#         return True

# class BaseGenericTypeChecker(TypeChecker):
#     """Type checker for base generic type"""

#     @property
#     def python_type(self):
#         """Given a type annotation or a class as input,
#         returns the corresponding python class.

#         Examples:
#             >>> python_type(typing.Dict)
#             <class 'dict'>
#             >>> python_type(typing.List[int])
#             <class 'list'>
#             >>> python_type(int)
#             <class 'int'>
#         """
#         try:
#             mro = self.type_.mro()
#         except AttributeError: # pragma: no cover
#           # if it doesn't have an mro method, it must be a weird typing object
#             return self.type_.__origin__

#         if typing.Type in mro: # pragma: no cover
#             return self.type_.python_type
#         if self.type_.__module__ == 'typing':
#             return self.type_.__origin__

#         return self.type_ # pragma: no cover

#     def is_typeof(self, value: typing.Any) -> bool:
#         """Check if a value is of this type"""
#         return isinstance(value, self.python_type)

# class IterableTypeChecker(UnionTypeChecker, BaseGenericTypeChecker):
#     """Type checker for iterable types"""

#     def is_typeof(self, value: typing.Any) -> bool:
#         """Check if a value is of this type"""
#         if not BaseGenericTypeChecker.is_typeof(self, value):
#             return False

#         subtype = self.subtypes[0]
#         return all(subtype.is_typeof(val) for val in value)

# class MappingTypeChecker(UnionTypeChecker, BaseGenericTypeChecker):
#     """Type checker for mapping types"""

#     def is_typeof(self, value: typing.Any) -> bool:
#         """Check if a value is of this type"""

#         if not BaseGenericTypeChecker.is_typeof(self, value):
#             return False

#         keytype, valtype = self.subtypes
#         return all(
#             keytype.is_typeof(key) and valtype.is_typeof(val)
#             for key, val in value.items()
#         )

# class TupleTypeChecker(UnionTypeChecker, BaseGenericTypeChecker):
#     """Type checker for Tuple"""

#     def is_typeof(self, value: typing.Any) -> bool:
#         """Check if a value is of this type"""

#         if not BaseGenericTypeChecker.is_typeof(self, value):
#             return False

#         return all(
#             valtype.is_typeof(val)
#             for val, valtype in zip(value, self.subtypes)
#         )

# def type_checker(type_: typing.Type) -> TypeChecker:
#     """TypeChecker distributor"""

#     if type_.__module__ == 'typing':
#         name = type_name(type_)
#         if name == 'Union':
#             return UnionTypeChecker(type_)
#         if name == 'Callable':
#             return CallableTypeChecker(type_)
#         if name == 'Any':
#             return AnyTypeChecker(type_)
#         if name == 'Type':
#             return TypeTypeChecker(type_)

#     if is_base_generic(type_):
#         return BaseGenericTypeChecker(type_)

#     if is_qualified_generic(type_):
#         name = type_name(type_)
#         if name in ITERABLE_TYPES:
#             return IterableTypeChecker(type_)

#         if name in MAPPING_TYPES:
#             return MappingTypeChecker(type_)

#         if name == 'Tuple':
#             return TupleTypeChecker(type_)

#     return TypeChecker(type_)
