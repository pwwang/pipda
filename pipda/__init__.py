"""A framework for data piping in python"""

from .symbolic import Symbolic
from .verb import register_verb, piping_sign
from .func import register_func
from .operators import register_operators, Operators

__version__ = '0.0.1'
