import ast
import functools
from typing import Type, Dict, Callable

from .verb import VerbCall

PIPING_OPS = {
    # op: (method, ast node, numpy ufunc name)
    ">>": ("__rrshift__", ast.RShift, "right_shift"),
    "|": ("__ror__", ast.BitOr, "bitwise_or"),
    "//": ("__rfloordiv__", ast.FloorDiv, "floor_divide"),
    "@": ("__rmatmul__", ast.MatMult, "matmul"),
    "%": ("__rmod__", ast.Mod, "remainder"),
    "&": ("__rand__", ast.BitAnd, "bitwise_and"),
    "^": ("__rxor__", ast.BitXor, "bitwise_xor"),
}

PATCHED_CLASSES: Dict[Type, Dict[str, Callable]] = {
    # kls:
    #    {}  # registered but not patched
    #    {"method": <method>, "imethod": <imethod>}  # patched
}


def _patch_cls_method(kls: Type, method: str) -> None:
    """Borrowed from https://github.com/sspipe/sspipe"""
    try:
        original = getattr(kls, method)
    except AttributeError:
        return

    PATCHED_CLASSES[kls][method] = original

    @functools.wraps(original)
    def wrapper(self, x, *args, **kwargs):
        if isinstance(x, VerbCall):
            return NotImplemented
        return original(self, x, *args, **kwargs)

    setattr(kls, method, wrapper)


def _unpatch_cls_method(kls: Type, method: str) -> None:
    if method in PATCHED_CLASSES[kls]:
        setattr(kls, method, PATCHED_CLASSES[kls].pop(method))


def _patch_cls_operator(kls: Type, op: str) -> None:
    method = PIPING_OPS[op][0].replace("__r", "__")
    imethod = PIPING_OPS[op][0].replace("__r", "__i")
    _patch_cls_method(kls, method)
    _patch_cls_method(kls, imethod)


def _unpatch_cls_operator(kls: Type, op: str) -> None:
    method = PIPING_OPS[op][0].replace("__r", "__")
    imethod = PIPING_OPS[op][0].replace("__r", "__i")
    _unpatch_cls_method(kls, method)
    _unpatch_cls_method(kls, imethod)


def patch_classes(*classes: Type) -> None:
    """Patch the classes in case it has piping operator defined

    For example, DataFrame.__or__ has already been defined, so we need to
    patch it to force it to use __ror__ of VerbCall if `|` is registered
    for piping.

    Args:
        classes: The classes to patch
    """
    for kls in classes:
        if kls not in PATCHED_CLASSES:
            PATCHED_CLASSES[kls] = {}

        if not PATCHED_CLASSES[kls]:
            _patch_cls_operator(kls, VerbCall.PIPING)


def unpatch_classes(*classes: Type) -> None:
    """Unpatch the classes

    Args:
        classes: The classes to unpatch
    """
    for kls in classes:
        if PATCHED_CLASSES[kls]:
            _unpatch_cls_operator(kls, VerbCall.PIPING)
        # Don't patch it in the future
        del PATCHED_CLASSES[kls]


def _patch_all(op: str) -> None:
    """Patch all registered classes that has the operator defined

    Args:
        op: The operator used for piping
            Avaiable:  ">>", "|", "//", "@", "%", "&" and "^"
        un: Unpatch the classes
    """
    for kls in PATCHED_CLASSES:
        _patch_cls_operator(kls, op)


def _unpatch_all(op: str) -> None:
    """Unpatch all registered classes

    Args:
        op: The operator used for piping
            Avaiable:  ">>", "|", "//", "@", "%", "&" and "^"
    """
    for kls in PATCHED_CLASSES:
        _unpatch_cls_operator(kls, op)


def _patch_default_classes() -> None:
    """Patch the default/commonly used classes"""

    try:
        import pandas
        patch_classes(
            pandas.DataFrame,
            pandas.Series,
            pandas.Index,
            pandas.Categorical,
        )
    except ImportError:
        pass

    try:  # pragma: no cover
        from modin import pandas
        patch_classes(
            pandas.DataFrame,
            pandas.Series,
            pandas.Index,
            pandas.Categorical,
        )
    except ImportError:
        pass

    try:  # pragma: no cover
        import torch
        patch_classes(torch.Tensor)
    except ImportError:
        pass

    try:  # pragma: no cover
        from django.db.models import query
        patch_classes(query.QuerySet)
    except ImportError:
        pass


def register_piping(op: str) -> None:
    """Register the piping operator for verbs

    Args:
        op: The operator used for piping
            Avaiable:  ">>", "|", "//", "@", "%", "&" and "^"
    """
    if op not in PIPING_OPS:
        raise ValueError(f"Unsupported piping operator: {op}")

    if VerbCall.PIPING:
        orig_method = VerbCall.__orig_opmethod__
        curr_method = PIPING_OPS[VerbCall.PIPING][0]
        setattr(VerbCall, curr_method, orig_method)
        _unpatch_all(VerbCall.PIPING)

    VerbCall.PIPING = op
    VerbCall.__orig_opmethod__ = getattr(VerbCall, PIPING_OPS[op][0])
    setattr(VerbCall, PIPING_OPS[op][0], VerbCall._pipda_eval)
    _patch_all(op)


register_piping(">>")
_patch_default_classes()
