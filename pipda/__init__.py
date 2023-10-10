from .context import Context, ContextBase
from .expression import Expression, register_array_ufunc
from .function import FunctionCall, register_func
from .operator import Operator, OperatorCall, register_operator
from .reference import ReferenceAttr, ReferenceItem
from .symbolic import Symbolic
from .utils import evaluate_expr
from .verb import VerbCall, register_verb
from .piping import register_piping, _patch_default_classes

__version__ = "0.13.1"

register_piping(">>")
_patch_default_classes()
