"""Provides register_function to register functions"""
from .utils import (
    Predicate,
    register_factory
)

class Function(Predicate):
    """The Function class"""

register_function = register_factory(Function) # pylint: disable=invalid-name
