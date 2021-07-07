"""Provide register_verb to register verbs"""

import typing

from .utils import has_expr
from .function import Function


class Verb(Function):
    """The verb class"""

    CURRENT_SIGN: typing.ClassVar[str] = ""


class FastEvalVerb(Function):
    """Verbs that can use its first argument to evaluate"""

    def _pipda_fast_eval(self):
        """Evaluate this verb function using the first argument"""
        if not self.args:
            return self

        firstarg, args = self.args[0], self.args[1:]
        if isinstance(firstarg, FastEvalVerb):
            firstarg = firstarg._pipda_fast_eval()

        if has_expr(firstarg):
            # if first argument is not data
            # copy self?
            self.dataarg = False
            return self

        return Function(self.func, args, self.kwargs)._pipda_eval(firstarg)
