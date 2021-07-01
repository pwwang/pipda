"""Provide register_verb to register verbs"""

from typing import ClassVar

from .function import Function


class Verb(Function):
    """The verb class"""
    CURRENT_SIGN: ClassVar[str] = None
