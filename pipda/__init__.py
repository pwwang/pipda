from .context import Context, ContextBase
from .expression import Expression, register_array_ufunc
from .function import FunctionCall, register_func
from .operator import Operator, OperatorCall, register_operator
from .reference import ReferenceAttr, ReferenceItem
from .symbolic import Symbolic
from .utils import evaluate_expr
from .verb import VerbCall, register_verb
from .piping import (
    register_piping,
    patch_classes,
    patch_django,
    patch_pandas,
    patch_polars,
    patch_torch,
)

__version__ = "0.13.2"

register_piping(">>")
patch_pandas()
patch_torch()
patch_django()
patch_polars()

__all__ = [
    "Context",
    "ContextBase",
    "Expression",
    "register_array_ufunc",
    "FunctionCall",
    "register_func",
    "patch_classes",
    "Operator",
    "OperatorCall",
    "register_operator",
    "ReferenceAttr",
    "ReferenceItem",
    "Symbolic",
    "evaluate_expr",
    "VerbCall",
    "register_verb",
    "register_piping",
]
