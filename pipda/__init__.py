"""A framework for data piping in python"""
# pylint: disable=unused-import
from .context import Context, ContextBase
from .expression import Expression
from .operator import Operator
from .symbolic import Symbolic
from .utils import DataEnv, evaluate_expr, functype
from .register import (
    register_func,
    register_operator,
    register_piping,
    register_verb,
    unregister,
)

__version__ = "0.4.0"
