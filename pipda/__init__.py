"""A framework for data piping in python"""
# pylint: disable=unused-import
from .symbolic import Symbolic
from .verb import register_verb, register_piping_sign
from .function import register_function
from .utils import Context, evaluate_args, evaluate_kwargs, evaluate_expr
from .operator import Operator, register_operator
from .common import register_common

__version__ = '0.1.0'
