"""Provide register_verb to register verbs"""
from typing import ClassVar

from .utils import (
    Predicate,
    PIPING_SIGNS,
    register_factory
)

class Verb(Predicate):
    """The verb class"""
    CURRENT_SIGN: ClassVar[str] = None

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
