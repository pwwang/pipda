"""Provide register_verb to register verbs"""

import typing
from .function import Function

class Verb(Function):
    """The verb class"""
    CURRENT_SIGN: typing.ClassVar[str] = ''
