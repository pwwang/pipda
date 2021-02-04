"""Provide register_verb to register verbs"""
from typing import Callable, ClassVar

from .utils import (
    Predicate,
    PIPING_SIGNS,
    register_factory,
    is_argument_node,
    get_verb_node
)

class Verb(Predicate):
    """The verb class"""

    CURRENT_SIGN: ClassVar[str] = None
    # used to remember the original operator function
    # when the sign is changed, we should get it back.
    ORIG_OP_FUNC: ClassVar[Callable] = None

    def is_piping(self):
        """Check if the verb is called in piping mode"""
        my_node, verb_node = get_verb_node()
        if my_node is verb_node:
            return True

        # or my_node is an argument of verb_node
        return is_argument_node(my_node, verb_node)

def register_piping_sign(sign: str):
    """Register a piping sign for the verbs"""
    if sign not in PIPING_SIGNS:
        raise ValueError(f"Unsupported piping sign: {sign}")

    if Verb.CURRENT_SIGN:
        current_sign = PIPING_SIGNS[Verb.CURRENT_SIGN]
        delattr(Verb, current_sign.method)

    Verb.CURRENT_SIGN = sign
    new_sign = PIPING_SIGNS[sign]
    setattr(Verb, new_sign.method, Verb.evaluate)

register_piping_sign('>>')

register_verb = register_factory(Verb) # pylint: disable=invalid-name
