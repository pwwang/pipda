"""Provides register_function to register functions"""
from .utils import (
    Predicate,
    register_factory,
    is_argument_node,
    get_verb_node
)

class Function(Predicate):
    """The Function class"""

    def is_piping(self) -> bool:
        """Check if the function should run in piping mode"""
        my_node, verb_node = get_verb_node()
        return is_argument_node(my_node, verb_node)

register_function = register_factory(Function) # pylint: disable=invalid-name
